from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/actividades")
def mostrar_actividades():
    deporte_fav = None

    busqueda = request.args.get("search", "").strip()
    solo_con_plaza = request.args.get("solo_con_plazas")
    deporte_fav = request.cookies.get("deporte_fav")

    coincidencias = Actividad.query

    if busqueda:
        coincidencias = coincidencias.filter(Actividad.nombre.ilike(f"%{busqueda}%"))
    if solo_con_plaza:
        coincidencias = coincidencias.filter(Actividad.plazas_libres > 0)

    actividades = coincidencias.all()

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):
    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.set_cookie(
        "deporte_fav",
        value=deporte,
        max_age=60 * 60 * 24 * 15,
        httponly=True,
        samesite="Lax",
    )
    return respuesta


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():
    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.delete_cookie("deporte_fav")
    return respuesta


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)

    # Hacemos la sesión permanente y obtenemos la lista (o [] si no existe)
    session.permanent = True
    reservas = session.get("reservas", [])

    # Comprobamos las 3 condiciones[cite: 26]
    if actividad.plazas_libres <= 0:
        flash("No quedan plazas libres en esta actividad.", "error")
    elif act_id in reservas:
        flash("Ya tienes esta actividad en tus reservas pendientes.", "error")
    elif len(reservas) >= 3:
        flash("Has alcanzado el límite máximo de 3 actividades.", "error")
    else:
        # Si cumple todo, añadimos el ID y actualizamos la sesión[cite: 26]
        reservas.append(act_id)
        session["reservas"] = reservas
        session.modified = True
        flash(f"'{actividad.nombre}' añadida a tus reservas pendientes.", "exito")

    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():
    lista_id_actividades_en_session = session.get("reservas", [])
    total_sin_descuento = 0.0
    if lista_id_actividades_en_session:
        actividades = Actividad.query.filter(
            Actividad.id.in_(lista_id_actividades_en_session)
        ).all()
        for n in actividades:
            total_sin_descuento += n.cuota
    else:
        actividades = []

    # Comprobamos si tiene 3 actividades y activamos el booleano
    if len(actividades) == 3:
        descuento_aplicado = True
        total_final = total_sin_descuento * 0.80  # Descuento del 20%
    else:
        descuento_aplicado = False
        total_final = total_sin_descuento

    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total_sin_descuento,
        descuento_aplicado=descuento_aplicado,
        total_final=total_final,
    )


@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):
    reservas = session.get("reservas", [])

    # Comprobamos que el ID esté en la lista antes de hacer .remove() para evitar errores
    if act_id in reservas:
        reservas.remove(act_id)
        session["reservas"] = reservas
        session.modified = True
        flash("Actividad eliminada de tus reservas pendientes.", "info")

    return redirect(url_for("public.ver_reservas"))


@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():
    reservas = session.get("reservas", [])

    if reservas:
        # Recuperamos todas las actividades seleccionadas
        actividades = Actividad.query.filter(Actividad.id.in_(reservas)).all()

        for actividad in actividades:
            # Nos aseguramos de que haya plazas antes de restar
            if actividad.plazas_libres > 0:
                actividad.plazas_libres -= 1

        db.session.commit()
        session.pop("reservas", None)
        flash("¡Inscripción confirmada! Tus plazas han sido reservadas.", "exito")

    return redirect(url_for("public.mostrar_actividades"))
