from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app.models import db, Usuario
from app.forms import LoginForm, RegistroForm, CambiarPasswordForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Ruta de Login 100 % funcional para pruebas independientes."""
    if current_user.is_authenticated:
        return redirect(url_for("public.mostrar_actividades"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.check_password(form.password.data):
            login_user(usuario, remember=form.remember.data)
            flash(f"¡Hola de nuevo, {usuario.username}!", "exito")

            siguiente_pagina = request.args.get("next")
            if siguiente_pagina and siguiente_pagina.startswith("/"):
                return redirect(siguiente_pagina)
            return redirect(url_for("public.mostrar_actividades"))
        else:
            flash("Correo electrónico o contraseña incorrectos.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("public.mostrar_actividades"))

    form = RegistroForm()
    if form.validate_on_submit():
        # 1. Instanciamos el Usuario con sus datos, su edad y el rol "socio"
        nuevo_usuario = Usuario(
            username=form.username.data,
            email=form.email.data,
            edad=form.edad.data,
            rol="socio",
        )
        # 2. Ciframos la contraseña usando el método set_password() del modelo
        nuevo_usuario.set_password(form.password.data)

        # 3. Guardamos en la base de datos y redirigimos al login
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Registro completado con éxito. Ya puedes iniciar sesión.", "exito")
        return redirect(url_for("auth.login"))

    return render_template("registro.html", form=form)


@auth_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    form = CambiarPasswordForm()
    if form.validate_on_submit():
        # 1. Comprobamos que la contraseña actual sea válida
        if not current_user.check_password(form.password_actual.data):
            flash("La contraseña actual es incorrecta.", "error")
        # 2. Comprobamos que la nueva sea diferente a la actual
        elif form.password_actual.data == form.nueva_password.data:
            flash("La nueva contraseña debe ser diferente a la actual.", "error")
        else:
            # 3. Actualizamos el hash y guardamos en BD
            current_user.set_password(form.nueva_password.data)
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "exito")
            return redirect(url_for("auth.perfil"))
    return render_template("perfil.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop(
        "reservas", None
    )  # Elimina las reservas pendientes sin lanzar KeyError si no existen
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("public.mostrar_actividades"))
