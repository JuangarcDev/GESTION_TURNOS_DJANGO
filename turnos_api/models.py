from django.db import models
from django.contrib.auth.models import User, AbstractBaseUser

# --------------------------------------
# TABLAS DE DOMINIO
# -------------------------------------

class TipoTurno(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class EstadoTurno(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class Proceso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre
    
class EstadoVentanilla(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre
    

# ---------------------------------------------
# MODELOS PRINCIPALES
# ---------------------------------------------

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.cedula}"
    
class Turno(models.Model):
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="turnos")
    turno = models.CharField(max_length=20)
    tipo_turno = models.ForeignKey(TipoTurno, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoTurno, on_delete=models.PROTECT)
    proceso = models.ForeignKey(Proceso, on_delete=models.PROTECT)
    fecha_turno = models.DateTimeField(auto_now_add=True)

    