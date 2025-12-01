import hvac

client = hvac.Client(url="http://localhost:8200")
client.auth.userpass.login(
    username="",
    password="",
)


def recursive_kv_path():
    def retrieve_path(mount_point: str = "secret", path: str = ""):
        if path != "" and path[-1] != "/":
            return [f"{mount_point}/data/{path}"]

        result = client.secrets.kv.v2.list_secrets(path=path, mount_point=mount_point)
        keys = result["data"]["keys"]

        all_paths = list()
        for key in keys:
            next_path = path + key
            leaf_path = retrieve_path(mount_point=mount_point, path=next_path)
            all_paths.extend(leaf_path)

        return all_paths

    return retrieve_path(mount_point="secret")


def backup_secret(paths: list, output: str = "set-kv.sh"):
    lines = list()
    for full_path in paths:
        try:
            # KV v2 대응: 'secret/data/aaa' → 'aaa'
            relative_path = full_path.replace('secret/data/', '')
            secret = client.secrets.kv.v2.read_secret_version(
                path=relative_path,
                mount_point='secret',
                raise_on_deleted_version=True
            )
            data = secret['data']['data']

            # key="value"로 변환
            kv_pairs = ' '.join([f'{k}="{v}"' for k, v in data.items()])

            # 최종 명령어 작성
            vault_cmd = f'docker exec vault vault kv put secret/{relative_path} {kv_pairs}'
            lines.append(vault_cmd)

            print(f"✅ 명령어 생성 완료: {relative_path}")

        except Exception as e:
            print(f"❌ 실패: {full_path} - {e}")

    with open(output, "w") as f:
        lines.insert(0, "#!/bin/bash")
        f.write("\n".join(lines))

backup_secret(paths=recursive_kv_path())
