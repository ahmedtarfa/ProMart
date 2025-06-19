from odoo.addons.bhs_password_policy.controllers.main import PasswordSecurityHome
from odoo.http import request, route
from odoo import _

class CustomAuthSignup(PasswordSecurityHome):
    def passwordless_signup(self):
        values = request.params
        qcontext = self.get_auth_signup_qcontext()

        password = values.get("password", "").strip()
        confirm_password = values.get("confirm_password", "").strip()

        # ✅ Confirm passwords match
        if password != confirm_password:
            qcontext["error"] = _("Passwords do not match. Please try again.")
            return request.render("auth_signup.signup", qcontext)

        # ✅ Check minimum length
        if len(password) < 6:
            qcontext["error"] = _("Please choose a password with at least 6 characters.")
            return request.render("auth_signup.signup", qcontext)

        # ✅ Validate with password policy (strength, etc.)
        try:
            request.env['res.users'].sudo()._check_password(password)
        except Exception as e:
            qcontext["error"] = str(e)
            return request.render("auth_signup.signup", qcontext)

        values["password"] = password
        values.pop("redirect", None)
        values.pop("token", None)

        sudo_users = request.env["res.users"].with_context(create_user=True).sudo()
        try:
            with request.cr.savepoint():
                sudo_users.signup(values, qcontext.get("token"))
        except Exception:
            qcontext["error"] = _("Could not create the user. Try again.")
            return request.render("auth_signup.signup", qcontext)

        return request.redirect("/web/login?msg=signup_success")
