from airflow.models import Variable
from airflow.exceptions import AirflowException
from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
from airflow.utils.context import Context
import requests


class SlackNotifier:
    def __init__(self, slack_webhook_conn_id="slack_default"):
        self.alert = SlackWebhookHook(slack_webhook_conn_id=slack_webhook_conn_id)
        self.env = Variable.get("ENV").upper()

    def get_yarn_app(self, app_name: str, yarn_api_url: str) -> str:
        try:
            response = requests.get(yarn_api_url, timeout=5)
            response.raise_for_status()
            apps = response.json().get("apps", {}).get("app", [])

            for app in apps:
                if app["name"] == app_name:
                    return app["trackingUrl"]

            raise AirflowException(f"App Name '{app_name}'을(를) 찾을 수 없습니다.")

        except (requests.Timeout, requests.ConnectionError, requests.HTTPError, requests.RequestException) as err:
            raise AirflowException(f"request error : {err}, request_url: {yarn_api_url}")

    def generate_blocks(self, dag_id: str, task_id: str, execution_date: str, message: str) -> dict:
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Dag ID* : `{dag_id}` \n *Task ID* : `{task_id}` \n *Execution Date* : `{execution_date}`",
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": message}},
        ]

    def slack_webhook(self, context: Context, message: str = ""):
        dag_id = context["task_instance"].dag_id
        task_id = context["task_instance"].task_id
        execution_date = context["execution_date"].strftime("%Y-%m-%d %H:%M:%S")
        text = f":airflow: *[{self.env}] Airflow Job Failed* :rotating_light:"
        if not message:
            message = f"{dag_id} Failed."
        blocks = self.generate_blocks(dag_id, task_id, execution_date, message)
        self.alert.send(text=text, blocks=blocks)

    def spark_failure(self, context: Context):
        dag_id = context["task_instance"].dag_id
        yarn_api_url = Variable.get("YARN_API_URL")

        try:
            log_url = self.get_yarn_app(dag_id, yarn_api_url)
        except AirflowException as err:
            log_url = f"YARN통신에 실패했습니다. : {err}"

        message = f"🔗 *Log URL* \n {log_url}"
        self.slack_webhook(context=context, message=message)
