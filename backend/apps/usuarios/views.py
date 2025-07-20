from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserRegisterSerializer, UserProfileSerializer, AdminUserUpdateSerializer
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# generar pago de matricula
from django.http import HttpRequest, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import urllib.request
import json



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        serializer = UserProfileSerializer(user)
        data['user'] = serializer.data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        """
        Permite a los administradores obtener información detallada de un usuario específico
        """
        if request.user.role != 'ADMINISTRATIVO':
            return Response(
                {"detail": "No tienes permiso para ver detalles de usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(id=user_id)
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, user_id):
        """
        Permite a los administradores actualizar la información de cualquier usuario
        """
        if request.user.role != 'ADMINISTRATIVO':
            return Response(
                {"detail": "No tienes permiso para actualizar usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener el usuario a actualizar
        try:
            user_to_update = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Actualizar el usuario usando el serializador con permisos de administrador
        serializer = AdminUserUpdateSerializer(user_to_update, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "detail": f"Usuario {user_to_update.username} actualizado correctamente.",
                "user": UserProfileSerializer(user_to_update).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, user_id):
        if request.user.role != 'ADMINISTRATIVO':
            return Response(
                {"detail": "No tienes permiso para eliminar usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )

        user_to_delete = get_object_or_404(User, id=user_id)
        username = user_to_delete.username
        user_to_delete.delete()

        return Response(
            {"detail": f"Usuario {username} eliminado correctamente."},
            status=status.HTTP_204_NO_CONTENT
        )


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['ADMINISTRATIVO', 'PROFESOR']:
            return Response(
                {"detail": "No tienes permiso para listar usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = User.objects.all()

        rol = request.query_params.get('rol')
        if rol:
            queryset = queryset.filter(role=rol)

        materia_id = request.query_params.get('materia')
        curso_id = request.query_params.get('curso')

        if materia_id and curso_id and rol == 'ESTUDIANTE':
            queryset = queryset.filter(curso__id=curso_id)
        elif curso_id and rol == 'ESTUDIANTE':
            queryset = queryset.filter(curso__id=curso_id)

        serializer = UserProfileSerializer(queryset, many=True)
        return Response(serializer.data)


class EstudiantesListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['ADMINISTRATIVO', 'PROFESOR']:
            return Response(
                {"detail": "No tienes permiso para listar estudiantes."},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = User.objects.filter(role='ESTUDIANTE')

        curso_id = request.query_params.get('curso')
        if curso_id:
            queryset = queryset.filter(curso__id=curso_id)

        serializer = UserProfileSerializer(queryset, many=True)
        return Response(serializer.data)



class GenerarQRPagoView(APIView):
    def post(self, request: HttpRequest):
        try:
            # Paso 1: Autenticación
            auth_data = json.dumps({
                "TokenService": "51247fae280c20410824977b0781453df59fad5b23bf2a0d14e884482f91e09078dbe5966e0b970ba696ec4caf9aa5661802935f86717c481f1670e63f35d5041c31d7cc6124be82afedc4fe926b806755efe678917468e31593a5f427c79cdf016b686fca0cb58eb145cf524f62088b57c6987b3bb3f30c2082b640d7c52907",
                    "TokenSecret": "9E7BC239DDC04F83B49FFDA5"
            }).encode("utf-8")

            auth_request = urllib.request.Request(
                url="https://serviciostigomoney.pagofacil.com.bo/api/servicio/login",
                data=auth_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(auth_request) as response:
                auth_response = json.loads(response.read().decode())
                access_token = auth_response.get("values")

            # Paso 2: Preparar datos para generar QR
            nro_pago = f"mat-{random.randint(100000, 999999)}"

            print("✅ Auth response:", auth_response)

            payload = {
                "tcCommerceID": "d029fa3a95e174a19934857f535eb9427d967218a36ea014b70ad704bc6c8d1c",
                "tcNroPago": nro_pago,
                "tcNombreUsuario": "Juan Pérez",
                "tnCiNit": 12345678,
                "tnTelefono": 71234567,
                "tcCorreo": "juan.perez@example.com",
                "tcCodigoClienteEmpresa": "C001",
                "tnMontoClienteEmpresa": "0.01",
                "tnMoneda": 2,
                "tcUrlCallBack": "https://backendaisiii-production.up.railway.app/api/usuarios/pagofacil/callback/",
                "tcUrlReturn": "https://tuservidor.com/retorno",
                "taPedidoDetalle": [
                    {
                        "Serial": 1,
                        "Producto": "Curso de Django",
                        "Cantidad": 1,
                        "Precio": "0.01",
                        "Descuento": 0,
                        "Total": "0.01"
                    }
                ]
            }

            print("✅ QR payload enviado:", payload)


            qr_request = urllib.request.Request(
                url="https://serviciostigomoney.pagofacil.com.bo/api/servicio/pagoqr",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                method="POST"
            )

            with urllib.request.urlopen(qr_request) as response:
                qr_response = json.loads(response.read().decode())
                print("✅ QR response recibido:", json.dumps(qr_response, indent=2))  # ← esto se imprimirá
                return JsonResponse(qr_response, status=200)


        except Exception as e:
            print("❌ ERROR al generar el QR:")
            print(f"Tipo de excepción: {exc_type.__name__}")
            print(f"Archivo: {filename}")
            print(f"Línea: {lineno}")
            print(f"Mensaje: {e}")
            print("🔍 Traceback completo:")
            print(traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)


#Preparar datos estáticos para el QR, con NroPago dinámico
class ConsultarTransaccionPagoFacilView(APIView):
    def post(self, request):
        try:
            transaccion_id = request.data.get("TransaccionDePago")
            if not transaccion_id:
                return JsonResponse({"error": "TransaccionDePago es requerido"}, status=400)

            payload = {
                "TransaccionDePago": transaccion_id
            }

            print("📨 Consultando transacción:", payload)

            consulta_request = urllib.request.Request(
                url="https://serviciostigomoney.pagofacil.com.bo/api/servicio/consultartransaccion",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(consulta_request) as response:
                resultado = json.loads(response.read().decode())
                print("📬 Respuesta de la consulta:", json.dumps(resultado, indent=2))
                return JsonResponse(resultado, status=200)

        except Exception as e:
            import traceback
            print("❌ ERROR al consultar transacción:")
            print(traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)



class PagoFacilCallbackView(APIView):
    def post(self, request):
        try:
            data = request.data
            print("📥 Callback recibido:", data)

            # Aquí podrías guardar en la base de datos si lo deseas

            return JsonResponse({
                "error": 0,
                "estatus": 1,
                "message": "Callback procesado correctamente",
                "values": True
            })

        except Exception as e:
            import traceback
            print("❌ ERROR en callback:")
            print(traceback.format_exc())
            return JsonResponse({
                "error": 1,
                "estatus": 0,
                "message": str(e),
                "values": False
            }, status=500)
