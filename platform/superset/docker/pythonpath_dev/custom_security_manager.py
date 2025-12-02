from superset.security import SupersetSecurityManager
from flask_appbuilder.security.views import AuthLDAPView
from flask_appbuilder.security.views import expose
from flask import g, redirect, flash, request
from flask_appbuilder.security.forms import LoginForm_db
from flask_login import login_user
from flask_appbuilder._compat import as_unicode
from flask_appbuilder.utils.base import get_safe_redirect

class AuthLocalAndLDAPView(AuthLDAPView):
    @expose("/login/", methods=["GET", "POST"])
    def login(self):
        if g.user is not None and g.user.is_authenticated:
            return redirect(self.appbuilder.get_url_for_index)
        form = LoginForm_db()
        if form.validate_on_submit():
            next_url = get_safe_redirect(request.args.get("next", ""))
            user = self.appbuilder.sm.auth_user_ldap(
                form.username.data, form.password.data
            )
            if not user:
                user = self.appbuilder.sm.auth_user_db(
                    form.username.data, form.password.data
                )
            if not user:
                flash(as_unicode(self.invalid_login_message), "warning")
                return redirect(self.appbuilder.get_url_for_login_with(next_url))
            login_user(user, remember=False)
            return redirect(next_url)
        return self.render_template(
            self.login_template, title=self.title, form=form, appbuilder=self.appbuilder
        )


class CustomSecurityManager(SupersetSecurityManager):
    authldapview = AuthLocalAndLDAPView

    def __init__(self, appbuilder):
        super(CustomSecurityManager, self).__init__(appbuilder)
