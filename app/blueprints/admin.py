import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def verificar_permisos_admin():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.es_monitor:
        abort(403)


@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()
    if form.validate_on_submit():
        nombre_imagen = None
        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data
            nombre_imagen = (
                form.deporte.data.lower() + "_" + secure_filename(archivo.filename)
            )

            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            archivo.save(
                os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_imagen)
            )

        nueva_actividad = Actividad(
            nombre=form.nombre.data,
            deporte=form.deporte.data,
            cuota=form.cuota.data,
            plazas_libres=form.plazas_libres.data,
            imagen=nombre_imagen,
        )
        db.session.add(nueva_actividad)
        db.session.commit()

        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad, actividad_id=actividad.id)
    if form.validate_on_submit():
        actividad.nombre = form.nombre.data
        actividad.deporte = form.deporte.data
        actividad.cuota = form.cuota.data
        actividad.plazas_libres = form.plazas_libres.data

        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data
            nombre_imagen = (
                form.deporte.data.lower() + "_" + secure_filename(archivo.filename)
            )

            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            archivo.save(
                os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_imagen)
            )

            if actividad.imagen and actividad.imagen != nombre_imagen:
                ruta_antigua = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], actividad.imagen
                )
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)

            actividad.imagen = nombre_imagen
        db.session.commit()
        return redirect(url_for("public.mostrar_catalogo"))

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)

    if actividad.plazas_libres == 0:
        flash("No se puede eliminar la actividad porque tiene el cupo lleno.", "error")
        return redirect(url_for("public.mostrar_actividades"))

    if actividad.imagen:
        ruta_imagen = os.path.join(
            current_app.config["UPLOAD_FOLDER"], actividad.imagen
        )
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

    db.session.delete(actividad)
    db.session.commit()

    flash("Actividad eliminada correctamente.", "exito")
    return redirect(url_for("public.mostrar_actividades"))
