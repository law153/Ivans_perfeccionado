from django.conf import settings
from django.shortcuts import render, redirect
from .models import Rol, Pregunta, Categoria, Consulta, Usuario, Producto, Venta, Detalle,  Detalle_comprado
from datetime import date, timedelta
from django.utils.translation import activate
from babel.dates import format_date
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate,login, logout
from django.core.files import File
import os
from django.contrib.auth.decorators import user_passes_test
# Create your views here.

#Django Webpypay
#-----------------------------------------------------------------------------------------------------------------------------
from transbank.webpay.webpay_plus.transaction import Transaction

def iniciar_transaccion(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            monto = request.POST.get('monto')
            orden_compra = request.POST.get('ordenCompra')
            session_id = request.POST.get('sessionId')
            return_url = request.build_absolute_uri('/confirmar_transaccion/')
            #final_url = request.build_absolute_uri('/fin_transaccion/')

            # Guardar el monto en la sesión
            request.session['monto'] = monto
            transaction = Transaction()
            response = transaction.create(orden_compra, session_id, monto, return_url)

            if response:
                return redirect(response['url'] + '?token_ws=' + response['token'])
            else:
                messages.warning(request,'Error al iniciar la transacción')
                return render(request, 'core/ErroresCarrito/errorCarrito.html')
        else:
            messages.warning(request,'Intente de nuevo')
            return render(request, 'core/cliente/metodo-pago.html')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def confirmar_transaccion(request):
    if request.user.is_authenticated:
        if 'token_ws' in request.GET:
            token = request.GET['token_ws']
            transaction = Transaction()
            response = transaction.commit(token)

            if response['status'] == 'AUTHORIZED':
                monto = request.session.get('monto')
                # A continuación la funcion de pagar el carrito fue agregada y asimilida por confirmar_transaccion
                username = request.session.get('username')
                usuarioC = Usuario.objects.get(correo = username)
                
                carritoP = Venta.objects.get(usuario = usuarioC, estado='ACTIVO')

                entrega = timedelta(3)

                fecha_compra = date.today() #carritoP.fecha_venta

                fecha_e_nueva = fecha_compra + entrega

                carritoP.fecha_entrega = fecha_e_nueva

                carritoP.save()

                detalles = Detalle.objects.filter(venta = carritoP)

                for d in detalles:
                    producto = Producto.objects.get(cod_prod = d.producto.cod_prod)
                    producto.stock -= d.cantidad
                    
                    Detalle_comprado.objects.create(nombre_prod_c = producto.nombre_prod,
                                                    cantidad_c = d.cantidad,
                                                    foto_prod_c = producto.foto_prod,
                                                    subtotal_c = d.subtotal,
                                                    venta_c = d.venta)


                    producto.save()

                carritoP.estado = 'VENTA'

                carritoP.carrito = 0

                carritoP.save()


                return render(request, 'core/cliente/exito-compra.html', {'response': response, 'monto': monto} )
            else:
                messages.warning(request, 'El pago ha sido rechazado')
                return render(request, 'core/ErroresCarrito/pagoRechazado.html')
        else:
            messages.warning(request,'No se recibió el token')
            return render(request, 'core/ErroresCarrito/errorCarrito.html')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    
def exitoCompra(request):
    if request.user.is_authenticated:
        return render(request, 'core/cliente/exito-compra.html')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')


#---------------------------------------------------------------------------------------------------------------------------



###Sobre errores
def mostrarError(request):
    return render(request, 'core/error.html')

def error_404(request, exception):
    messages.warning(request,'Esa pagina no existe :/')
    return redirect('mostrarError')


###Paginas sin-cuenta###
def mostrarIndex(request):
    categoria = Categoria.objects.all()
    
    contexto = {"categorias" : categoria}

    return render(request, 'core/index.html',contexto)


def mostrarNosotros(request):
    categoria = Categoria.objects.all()

    contexto = {"categorias" : categoria}

    return render(request, 'core/sin-cuenta/nosotros.html',contexto)

def mostrarRegistro(request):
    categoria = Categoria.objects.all()
    preguntaObjeto = Pregunta.objects.all()

    contexto = {"categorias" : categoria,
                "pregunta" : preguntaObjeto}

    return render(request, 'core/sin-cuenta/registrarse.html',contexto)

def mostrarIni_sesion(request):
    categoria = Categoria.objects.all()

    contexto = {"categorias" : categoria}

    return render(request, 'core/sin-cuenta/inicio-sesion.html',contexto)

def mostrarOlv_contra(request):

    if request.user.is_authenticated:
        categoria = Categoria.objects.all()

        contexto = {"categorias" : categoria}
        return render(request, 'core/sin-cuenta/olvidar-contrasena.html',contexto)
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarError')

def mostrarPregunta(request):
    categoria = Categoria.objects.all()
    pregunta = Pregunta.objects.all()

    contexto = {"categorias" : categoria,
                "preguntas" : pregunta}
    return render(request, 'core/sin-cuenta/Pregunta.html',contexto)

def mostrarProducto(request, id_prod):
    categoria = Categoria.objects.all() 

    producto = Producto.objects.get(cod_prod = id_prod)
    
    contexto = {"product" : producto, "categorias" : categoria}

    return render(request, 'core/sin-cuenta/Producto.html',contexto)

def mostrarCategoria(request, id_cate):
    categoria = Categoria.objects.all()

    cate = Categoria.objects.get(id_categoria = id_cate)

    productos = Producto.objects.filter(categoria = cate)
    
    contexto = {"products" : productos ,"categorias" : categoria, "categoria" : cate}

    return render(request, 'core/sin-cuenta/Categoria.html',contexto)


def registrarUsuario(request):
    rutU = request.POST['rut']
    dvrutU = request.POST['dvrut']
    nombreU = request.POST['nombre']
    apellidoU = request.POST['apellido']
    telefonoU = request.POST['fono']
    direccionU = request.POST['direc']
    correoU = request.POST['correo_reg']
    claveU = request.POST['contra_ini']
    respuestaU = request.POST['respuesta']
    preguntaUid = request.POST['pregunta']

    registroRol = Rol.objects.get(id_rol = 1) ##Los usuarios registrados son clientes
    registroPregunta = Pregunta.objects.get(id_pregunta = preguntaUid) ##Pregunta asiganada por defecto

    usuario1 = Usuario.objects.filter(rut = rutU)
    usuario2 = Usuario.objects.filter(correo = correoU)

    if usuario1 or usuario2:
        messages.error(request,'Ya existe una cuenta con el correo/rut ingresado')
        return redirect('mostrarRegistro')
    else:
        Usuario.objects.create( rut = rutU,
                                dvrut = dvrutU,
                                nombre = nombreU,
                                apellido = apellidoU,
                                telefono = telefonoU,
                                correo = correoU,
                                clave = claveU,
                                direccion = direccionU,
                                respuesta = respuestaU,
                                rol = registroRol,
                                pregunta = registroPregunta)
        
        user = User.objects.create_user(username = correoU, email = correoU, password = claveU )
        user.is_staff = False
        user.is_active = True
        user.save()

        return redirect('mostrarIni_sesion')

def consultar(request):
    
    nombreC = request.POST['nom-ap']
    asuntoC = request.POST['asunto']
    mensajeC = request.POST['msg']

    Consulta.objects.create(nombre_consultante = nombreC,
                            asunto_consulta = asuntoC,
                            mensaje_consulta = mensajeC)
    messages.success(request,'Se ha enviado el mensaje')
    return redirect('mostrarNosotros')

def inicioSesion(request):
    
    correoI = request.POST['correo_ini']
    claveI = request.POST['contra_ini']

    try:
        user1 = User.objects.get(username = correoI)
    except User.DoesNotExist:
        messages.error(request,'El usuario o la contraseña son incorrectos')
        return redirect('mostrarIni_sesion')
    
    pass_valida = check_password(claveI, user1.password)
    if not pass_valida:
        messages.error(request,'El usuario o la contraseña son incorrectos')
        return redirect('mostrarIni_sesion')
    usuario = Usuario.objects.get(correo = correoI, clave = claveI)
    user = authenticate(username = correoI, password = claveI)
    if user is not None:
        login(request, user)
        if(usuario.rol.id_rol == 1):
            request.session['username'] = user1.username
            return redirect('mostrarIndexCli')
        else:
            request.session['username'] = user1.username
            return redirect('mostrarIndexAdm')
    else:
        messages.error(request,'El usuario no existe')
        return redirect('mostrarIni_sesion')
    
def cierreSesion(request):
    logout(request)
    return redirect('mostrarIndex')

def revisarDatos(request):
    rutR = request.POST['rut']
    dvrutR = request.POST['dvrut']
    idPreguntaR = request.POST['pregunta']
    respuestaR = request.POST['respuesta']


    try:    
        usuario = Usuario.objects.get(rut = rutR)
    except Usuario.DoesNotExist:
        messages.error(request,'El rut no está registrado')
        return redirect('mostrarPregunta')

    if str(usuario.dvrut) == str(dvrutR):

        preguntaR = Pregunta.objects.get(id_pregunta = idPreguntaR)
        if str(usuario.pregunta).strip().lower() == str(preguntaR).strip().lower() and str(usuario.respuesta).strip().lower() == str(respuestaR).strip().lower():
            user = User.objects.get(username = usuario.correo)
            login(request, user)
            request.session['username'] = user.username 
            return redirect('mostrarOlv_contra')
        else:
            messages.error(request,'La pregunta o respuesta no son correctas')
            return redirect('mostrarPregunta')
    else:
        messages.error(request,'El digito verificador no es correcto')
        return redirect('mostrarPregunta')
    
def olvideClave(request):
    usernameP = request.session.get('username')
    usuario = Usuario.objects.get(correo = usernameP)
    user = User.objects.get(username = usernameP)

    contraN = request.POST['contra_nueva']

    usuario.clave = contraN
    user.set_password(contraN)

    usuario.save()
    user.save()

    messages.success(request,'Contraseña reestablecida correctamente')
    return redirect('cierreSesion')  
        

###Paginas cliente###
def mostrarProductoCli(request, id_prod):

    if request.user.is_authenticated:
        categoria = Categoria.objects.all() 

        producto = Producto.objects.get(cod_prod = id_prod)
        
        contexto = {"product" : producto, "categorias" : categoria}

        return render(request, 'core/cliente/Producto-cli.html',contexto)
    
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarCategoriaCli(request, id_cate):
        
    if request.user.is_authenticated:

        categoria = Categoria.objects.all()

        cate = Categoria.objects.get(id_categoria = id_cate)

        productos = Producto.objects.filter(categoria = cate)
        
        contexto = {"products" : productos ,"categorias" : categoria, "categoria" : cate}

        return render(request, 'core/cliente/Categoria-cli.html', contexto)
    
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarMetodoPago(request, id_compra):

    if request.user.is_authenticated:

        categoria = Categoria.objects.all()

        username = request.session.get('username')
        usuario1 = Usuario.objects.get(correo = username)

        carrito = Venta.objects.filter(usuario = usuario1, estado='ACTIVO').first()

        if carrito:
            cart = Venta.objects.filter(id_venta = id_compra)
        
            contexto = {"categorias" : categoria, "venta" : cart}
            return render(request, 'core/cliente/Metodo-pago.html',contexto)
        
        else:
            contexto = {"categorias" : categoria}
        return render(request, 'core/cliente/Metodo-pago.html',contexto)

    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarNosotrosCli(request):
    if request.user.is_authenticated:
        categoria = Categoria.objects.all()
        
        contexto = {"categorias" : categoria}
        return render(request, 'core/cliente/nosotros-cli.html',contexto)
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarPerfilCli(request):
    if request.user.is_authenticated:
        categoria = Categoria.objects.all()

        username = request.session.get('username')
        usuario = Usuario.objects.get(correo = username)

        contexto = {
            "user" : usuario,
            "categorias" : categoria
        }

        return render(request, 'core/cliente/Perfil.html',contexto)
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarIndexCli(request):
    if request.user.is_authenticated:

        categoria = Categoria.objects.all()

        username = request.session.get('username')
        usuario1 = Usuario.objects.get(correo = username)

        carrito = Venta.objects.filter(usuario = usuario1, estado='ACTIVO').first()

        if carrito:
            detalles = Detalle.objects.filter(venta = carrito)
            for i in detalles:
                if i.producto.stock <= 0:
                    i.delete()
                    messages.warning(request,'Un producto de su carrito se quedó sin stock')
                    return redirect('mostrarCarritoCli')
                    
            carrito.save()
            if not detalles:
                carrito.estado = 'INACTIVO'
                carrito.save()
        
        contexto = {"categorias" : categoria}
        return render(request, 'core/cliente/index-cli.html',contexto)
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarCarritoCli(request):
    if request.user.is_authenticated:

        categoria = Categoria.objects.all()

        username = request.session.get('username')
        usuario1 = Usuario.objects.get(correo = username)

        carrito = Venta.objects.filter(usuario = usuario1, estado='ACTIVO').first()

        if carrito:
            detalles = Detalle.objects.filter(venta = carrito)
            totalV = 0
            for i in detalles:

                if i.producto.stock <= 0:
                    i.delete()
                    messages.warning(request,'Un producto de su carrito se quedó sin stock')
                    return redirect('mostrarCarritoCli')
                    
                totalV += i.subtotal
            carrito.total = totalV
            carrito.save()
            contexto = {"categorias" : categoria,
                        "carrito" : detalles,
                        "venta" : carrito}
            if not detalles:
                carrito.estado = 'INACTIVO'
                carrito.save()
        else:
            contexto = {"categorias" : categoria}
            messages.warning(request,'No hay productos en el carrito actualmente')
        
        return render(request, 'core/cliente/carrito.html',contexto)
    
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarCambioContraCli(request):
    if request.user.is_authenticated:
        categoria = Categoria.objects.all()
        
        contexto = {"categorias" : categoria}
        return render(request, 'core/cliente/cambiar-contrasena-cli.html',contexto)
    
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarEditarPerfilCli(request):
    if request.user.is_authenticated:
        categoria = Categoria.objects.all()

        username = request.session.get('username')

        usuario = Usuario.objects.get(correo = username)

        preguntaObjeto = Pregunta.objects.all()

        contexto = {
            "user" : usuario,
            "pregunta": preguntaObjeto,
            "categorias" : categoria
        }
        
        return render(request, 'core/cliente/Editar-perfil.html',contexto)
    
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def mostrarHistorial(request):
    if request.user.is_authenticated:

        activate('es')

        categoria = Categoria.objects.all()

        username = request.session.get('username')
        usuario1 = Usuario.objects.get(correo = username)

        compras = Venta.objects.filter(usuario = usuario1, estado='VENTA') | Venta.objects.filter(usuario = usuario1, estado='Cancelado')

        if compras:
            historial_formateado = []

            for compra in compras:
                fecha_venta_es = format_date(compra.fecha_venta, format='medium', locale='es')
                fecha_entrega_es = format_date(compra.fecha_entrega, format='medium', locale='es')
                historial_formateado.append((compra, fecha_venta_es, fecha_entrega_es))

            contexto = {"categorias" : categoria,
                        "historial" : historial_formateado}
        else:
            contexto = {"categorias" : categoria}
            messages.warning(request,'No tiene compras previas')
        
        return render(request, 'core/cliente/historial.html',contexto)
    
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    
def mostrarCompra(request, idVenta):
    if request.user.is_authenticated:

        categoria = Categoria.objects.all()

        username = request.session.get('username')
        usuario1 = Usuario.objects.get(correo = username)

        carrito = Venta.objects.get(id_venta = idVenta, usuario = usuario1)
        
        detalles = Detalle_comprado.objects.filter(venta_c = carrito)

        fecha_venta_esp = format_date(carrito.fecha_venta, format='short', locale='es')
        fecha_entrega_esp = format_date(carrito.fecha_entrega, format='short', locale='es')

        contexto = {"categorias" : categoria,
                    "carrito" : detalles,
                    "venta" : carrito,
                    "fecha_venta_es": fecha_venta_esp,
                    "fecha_entrega_es": fecha_entrega_esp}
        
        return render(request, 'core/cliente/compra.html',contexto)
    
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def editarPerfilCli(request):
    if request.user.is_authenticated:

        usernameP = request.session.get('username')

        nombreU = request.POST['nombre']
        apellidoU = request.POST['apellido']
        rutU = request.POST['rut']
        dvrutU = request.POST['dvrut']
        telefonoU = request.POST['telefono']
        direccionU = request.POST['direccion']
        correoU = request.POST['correo']
        idpreguntaU = request.POST['pregunta']
        respuestaU = request.POST['respuesta']

        usuario = Usuario.objects.get(correo = usernameP)
        usuario2 = User.objects.get(username = usuario.correo)

        fotoU = request.FILES.get('imagen',usuario.foto_usuario)

        if Usuario.objects.filter(rut = rutU).exclude(id_usuario = usuario.id_usuario).exists():
            messages.error(request, 'Ya existe un usuario con ese RUT.')
            return redirect('mostrarEditarPerfilCli')
        
        if Usuario.objects.filter(correo = correoU).exclude(correo = usuario.correo).exists():
            messages.error(request, 'Ya existe un usuario con ese correo.')
            return redirect('mostrarEditarPerfilCli')

        usuario.rut = rutU
        usuario.dvrut = dvrutU
        usuario.nombre = nombreU
        usuario.apellido = apellidoU
        usuario.telefono = telefonoU
        usuario.correo = correoU
        usuario.direccion = direccionU
        usuario.respuesta = respuestaU
        usuario.foto_usuario = fotoU
        registroPregunta = Pregunta.objects.get(id_pregunta = idpreguntaU)
        usuario.pregunta = registroPregunta

        usuario2.username = correoU
        usuario2.email = correoU

        usuario.save()
        usuario2.save()

        messages.success(request,'Perfil editado correctamente (o no cambió nada)')        
        return redirect('mostrarPerfilCli')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def eliminarCuenta(request,id_user):
    if request.user.is_authenticated:
        usuario = Usuario.objects.get(id_usuario = id_user)
        user = User.objects.get(username = usuario.correo)
        usuario.delete()
        user.delete()

        messages.success(request,'Cuenta borrada exitosamente')
        return redirect('mostrarIndex')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def agregarAlCarrito(request):
    if request.user.is_authenticated:

        cod_produc = request.POST['id_product']
        productoC = Producto.objects.get(cod_prod = cod_produc)

        username = request.session.get('username')
        usuarioC = Usuario.objects.get(correo = username)
        
        fecha_hoy = date.today()
        entrega = timedelta(999)
        fecha_e = fecha_hoy + entrega

        carrito = Venta.objects.filter(usuario = usuarioC, estado='ACTIVO').first()

        if carrito:
            detalle1 = Detalle.objects.filter(venta = carrito, producto = productoC)
            if detalle1:
                detalle = Detalle.objects.get(venta = carrito, producto = productoC)
                detalle.cantidad += 1
                detalle.subtotal += productoC.precio
                detalle.save()

                
            else:
                Detalle.objects.create(cantidad = 1,
                                        subtotal = productoC.precio,
                                        venta = carrito,
                                        producto = productoC)


        else:
            carrito = Venta.objects.create(fecha_venta = fecha_hoy,
                                        estado = "ACTIVO",
                                        fecha_entrega = fecha_e,
                                        total = productoC.precio,
                                        carrito = 1,
                                        usuario = usuarioC)

            Detalle.objects.create(cantidad = 1,
                                    subtotal = productoC.precio,
                                    venta = carrito,
                                    producto = productoC)
            
        return redirect('mostrarCarritoCli')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def sacarDelCarro(request, cod_detalle):
    if request.user.is_authenticated:
        detalle = Detalle.objects.get(id_detalle = cod_detalle)
        detalle.delete()
        

        return redirect('mostrarCarritoCli')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def cambiarCantidad(request, cod_detalle):
    if request.user.is_authenticated:
        detalle = Detalle.objects.get(id_detalle = cod_detalle)
        cant = int(request.POST['nueva_cantidad_{}'.format(cod_detalle)])
        producto = Producto.objects.get(cod_prod = detalle.producto.cod_prod)

        stockC = producto.stock
        cantidadC = int(cant)

        if cantidadC >= 0:
            if cantidadC <= stockC:
                detalle.cantidad = cantidadC
                detalle.subtotal = detalle.producto.precio * cantidadC
                detalle.save()
                return redirect('mostrarCarritoCli')
            else:
                messages.warning(request,'La cantidad no puede exceder el stock disponible')
                return redirect('mostrarCarritoCli')
        else:
            messages.warning(request,'La cantidad no puede ser menor a 1')
            return redirect('mostrarCarritoCli')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

def consultarCli(request):
    if request.user.is_authenticated:
        username = request.session.get('username')
        usuario = Usuario.objects.get(correo = username)


        asuntoC = request.POST['asunto']
        mensajeC = request.POST['msg']

        Consulta.objects.create(nombre_consultante = usuario.nombre,
                                asunto_consulta = asuntoC,
                                mensaje_consulta = mensajeC)
        messages.success(request,'Se ha enviado el mensaje')
        return redirect('mostrarNosotrosCli')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')


def cambiarClaveCli(request):
    if request.user.is_authenticated:
        usernameP = request.session.get('username')
        contraA = request.POST['contra_actual']
        contraN = request.POST['contra_nueva']

        usuario = Usuario.objects.get(correo = usernameP)
        usuario2 = User.objects.get(username = usuario.correo)
        if str(usuario.clave) == str(contraA):

            usuario.clave = contraN
            usuario2.set_password(contraN)

            usuario.save()
            usuario2.save()
            messages.success(request,'Contraseña cambiada correctamente')
            return redirect('cierreSesion')

        else:
            messages.error(request,'La contraseña actual es incorrecta')
            return redirect('mostrarCambioContraCli')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    
def cancelarPedido(request, idVenta):
    if request.user.is_authenticated:

        username = request.session.get('username')
        usuario1 = Usuario.objects.get(correo = username)

        compra = Venta.objects.get(id_venta = idVenta, usuario = usuario1)

        hoy = date.today()

        if compra.fecha_entrega <= hoy:

            messages.success(request,'Ya no puede cancelar su pedido')
            return redirect('mostrarHistorial')
        else:
            compra.estado = 'Cancelado'

            compra.save()

            detalles = Detalle.objects.filter(venta = compra)

            for i in detalles:
                product = i.producto
                cant = i.cantidad
                productou = Producto.objects.get(cod_prod = product.cod_prod)
                productou.stock += cant
                productou.save()
            
            messages.success(request,'Pedido cancelado')
            return redirect('mostrarHistorial')
    
    else:

        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

    

###Paginas admin###


def mostrarIndexAdm(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()
            
            contexto = {"categorias" : categoria}
            return render(request, 'core/administrador/index-adm.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    

def mostrarPerfilAdm(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()

            username = request.session.get('username')
            usuario = Usuario.objects.get(correo = username)

            contexto = {
                "user" : usuario,
                "categorias" : categoria
            }

            return render(request, 'core/administrador/perfil-adm.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    

def mostrarCategoriaAdm(request, id_cate):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()

            cate = Categoria.objects.get(id_categoria = id_cate)

            productos = Producto.objects.filter(categoria = cate)
            
            contexto = {"products" : productos ,"categorias" : categoria, "categoria" : cate}

            return render(request, 'core/administrador/categoria-adm.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    

def mostrarAgregar(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categories = Categoria.objects.all()
            contexto = {
                "categorias" : categories
            }
            return render(request, 'core/administrador/Agregar.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    

def mostrarEditarPerfilAdm(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()

            username = request.session.get('username')
            usuario = Usuario.objects.get(correo = username)

            preguntaObjeto = Pregunta.objects.all()

            contexto = {
                "user" : usuario,
                "pregunta": preguntaObjeto,
                "categorias" : categoria
            }
            
            return render(request, 'core/administrador/Editar-perfil-adm.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    

def mostrarCambioContraAdm(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()
            
            contexto = {"categorias" : categoria}
            return render(request, 'core/administrador/cambiar-contrasena-adm.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    

def mostrarProductoAdm(request,id_prod):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all() 

            producto = Producto.objects.get(cod_prod = id_prod)
            
            contexto = {
                "product" : producto,
                "categorias" : categoria
            }

            return render(request, 'core/administrador/producto-adm.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
    
 
def mostrarEditarRol(request):
    if request.user.is_authenticated:
        if request.user.is_staff:

            username = request.session.get('username')
            usuario = Usuario.objects.get(correo = username)

            categoria = Categoria.objects.all()
            clientes = Usuario.objects.exclude(id_usuario = usuario.id_usuario)

            contexto = {
                "clients": clientes,
                "categorias": categoria
            }
            return render(request, 'core/administrador/Editar-rol.html',contexto)
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta página')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta página')
        return redirect('mostrarIni_sesion')
    
def mostrarConsultas(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()
            consultas = Consulta.objects.all()

            contexto = {
                "categorias": categoria,
                "consulta": consultas
            }
            return render(request, 'core/administrador/consultas.html', contexto)
        else:
            messages.warning(request, 'Debe ser una administrador para acceder a esta página')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta página')
        return redirect('mostrarIni_sesion')

def mostrarDetallePedido(request, idPedido):
    if request.user.is_authenticated:
        if request.user.is_staff:
            categoria = Categoria.objects.all()

            carrito = Venta.objects.get(id_venta = idPedido)
            detalles = Detalle_comprado.objects.filter(venta_c = carrito)

            fecha_pedido_es = format_date(carrito.fecha_venta, format='short', locale='es')
            fecha_entrega_es = format_date(carrito.fecha_entrega, format='short', locale='es')

            contexto = {
                "categorias": categoria,
                "carrito": detalles,
                "pedido": carrito,
                "fecha_pedido": fecha_pedido_es,
                "fecha_entrega": fecha_entrega_es
            }
            return render(request, 'core/administrador/pedido.html',contexto)
        else:
            messages.warning(request,'Debe ser una administrador para acceder a esta página')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion') 
    

def mostrarPedidos(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            activate('es')
            categoria = Categoria.objects.all()

            pedidos = Venta.objects.filter(estado = 'VENTA')
            
            if pedidos:
                l_pedidos_formateado=[]
                for pedido in pedidos:
                    fecha_pedido_es = format_date(pedido.fecha_venta, format='medium', locale='es')
                    fecha_entrega_es = format_date(pedido.fecha_entrega, format='medium', locale='es')
                    l_pedidos_formateado.append((pedido, fecha_pedido_es, fecha_entrega_es))
                
                contexto = {
                    "categorias": categoria,
                    "l_pedido": l_pedidos_formateado
                }
            else:
                contexto = {"categorias" : categoria}
                messages.warning(request,'No hay pedidos registrados')
            return render(request, 'core/administrador/Listado-Pedidos.html',contexto)
        else:
            messages.warning(request,'Debe ser una administrador para acceder a esta página')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')    
 
def agregarProducto(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            nombreP = request.POST['nombre']
            descripcionP = request.POST['descripcion']
            precioP = request.POST['precio']
            stockP = request.POST['stock']
            fotoP = request.FILES['imagen']
            unidadP = request.POST['medida']
            categoriaP = request.POST['categoria']

            registroCategoria = Categoria.objects.get(id_categoria = categoriaP)

            prodTest = Producto.objects.filter(nombre_prod = nombreP, categoria = registroCategoria).first()

            if prodTest:
                messages.success(request,'Ya existe un producto con el mismo nombre y categoria')
                return redirect('mostrarAgregar')
            else:
                Producto.objects.create(nombre_prod = nombreP, descripcion = descripcionP, precio = precioP, stock = stockP, foto_prod = fotoP, unidad_medida = unidadP, categoria = registroCategoria)
                messages.success(request,'El producto fue agregado correctamente')
                return redirect('mostrarAgregar')
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

 
def editarProducto(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            codigoP = request.POST['id']
            nombreP = request.POST['nombre']
            descripcionP = request.POST['descripcion']
            precioP = request.POST['precio']
            stockP = request.POST['stock']
            unidadP = request.POST['medida']
            categoriaP = request.POST['categoria']
            registroCategoria = Categoria.objects.get(id_categoria = categoriaP)


            producto = Producto.objects.get(cod_prod = codigoP)

            fotoP = request.FILES.get('imagen',producto.foto_prod)



            if Producto.objects.filter(nombre_prod = nombreP, categoria = registroCategoria).exclude(cod_prod = producto.cod_prod).exists():
                messages.success(request,'Ya existe un producto con el mismo nombre y categoria')
                return redirect('mostrarAgregar')
                
            producto.nombre_prod = nombreP
            producto.descripcion = descripcionP
            producto.precio = precioP
            producto.stock = stockP
            producto.foto_prod = fotoP
            producto.unidad_medida = unidadP
            producto.categoria = registroCategoria
            producto.save()
            messages.success(request,'El producto fue editado correctamente')
                
            return redirect('mostrarIndexAdm')
            
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

 
def eliminarProducto(request,id_prod):
    if request.user.is_authenticated:
        if request.user.is_staff:
            producto = Producto.objects.get(cod_prod = id_prod)
            producto.delete()
            messages.error(request,'Producto eliminado')
            return redirect('mostrarIndexAdm')
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

 
def editarPerfilAdm(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            usernameP = request.session.get('username')

            nombreU = request.POST['nombre']
            apellidoU = request.POST['apellido']
            rutU = request.POST['rut']
            dvrutU = request.POST['dvrut']
            telefonoU = request.POST['telefono']
            direccionU = request.POST['direccion']
            correoU = request.POST['correo']
            idpreguntaU = request.POST['pregunta']
            respuestaU = request.POST['respuesta']

            usuario = Usuario.objects.get(correo = usernameP)
            usuario2 = User.objects.get(username = usuario.correo)

            fotoU = request.FILES.get('imagen',usuario.foto_usuario)

            if Usuario.objects.filter(rut = rutU).exclude(id_usuario = usuario.id_usuario).exists():
                messages.error(request, 'Ya existe un usuario con ese RUT.')
                return redirect('mostrarEditarPerfilAdm')
            
            if Usuario.objects.filter(correo = correoU).exclude(correo = usuario.correo).exists():
                messages.error(request, 'Ya existe un usuario con ese correo.')
                return redirect('mostrarEditarPerfilAdm')

            usuario.rut = rutU
            usuario.dvrut = dvrutU
            usuario.nombre = nombreU
            usuario.apellido = apellidoU
            usuario.telefono = telefonoU
            usuario.correo = correoU
            usuario.direccion = direccionU
            usuario.respuesta = respuestaU
            usuario.foto_usuario = fotoU
            registroPregunta = Pregunta.objects.get(id_pregunta = idpreguntaU)
            usuario.pregunta = registroPregunta

            usuario2.username = correoU
            usuario2.email = correoU

            usuario.save()
            usuario2.save()
            messages.success(request,'Perfil editado correctamente (o no cambió nada)')
            
            return redirect('mostrarPerfilAdm')
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

 
def cambiarClaveAdm(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            usernameP = request.session.get('username')
            contraA = request.POST['contra_actual']
            contraN = request.POST['contra_nueva']

            usuario = Usuario.objects.get(correo = usernameP)
            usuario2 = User.objects.get(username = usuario.correo)

            if str(usuario.clave) == str(contraA):

                usuario.clave = contraN
                usuario2.set_password(contraN)
                usuario.save()
                usuario2.save()
                messages.success(request,'Contraseña cambiada correctamente')
                return redirect('cierreSesion')

            else:
                messages.error(request,'La contraseña actual es incorrecta')
                return redirect('mostrarCambioContraAdm')
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')

 
def editarRol(request,id):
    if request.user.is_authenticated:
        if request.user.is_staff:
            usuario = Usuario.objects.get(id_usuario = id)
            usuario2 = User.objects.get(username = usuario.correo)

            if usuario.rol.id_rol == 1:
                registrolRol = Rol.objects.get(id_rol = 2)
                usuario.rol = registrolRol
                usuario2.is_staff = True
            else:
                registrolRol = Rol.objects.get(id_rol = 1)
                usuario.rol = registrolRol
                usuario2.is_staff = False
            
            usuario.save()
            usuario2.save()
            messages.success(request,"Rol cambiado con éxito")
            return redirect('mostrarEditarRol')
        else:
            messages.warning(request,'Debe ser un administrador para acceder a esta pagina')
            return redirect('mostrarIni_sesion')
            
    else:
        messages.warning(request,'Debe estar registrado para acceder a esta pagina')
        return redirect('mostrarIni_sesion')
def errorCarrito(request):
    return render(request, 'errorCarrito.html')

def pagoRechazado(request):
    return render(request, 'pagoRechazado.html')
    




