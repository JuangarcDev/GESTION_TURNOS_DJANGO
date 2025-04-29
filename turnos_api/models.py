from django.db import models
from django.contrib.auth.models import User, AbstractBaseUser

# --------------------------------------
# TABLAS DE DOMINIO
# --------------------------------------

class TipoTurno(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class EstadoTurno(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class TipoTramite(models.Model):
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
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} - {self.apellidos} - {self.cedula}"
    
class Turno(models.Model):
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="turnos")
    turno = models.CharField(max_length=20)
    tipo_turno = models.ForeignKey(TipoTurno, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoTurno, on_delete=models.PROTECT)
    tipo_tramite = models.ForeignKey(TipoTramite, on_delete=models.PROTECT)
    fecha_turno = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Turno {self.turno} - {self.estado.nombre}"
    
class Funcionario(models.Model):
    usuario = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_edicion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre
    
class Atencion(models.Model):
    id_funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name="atenciones")
    id_turno = models.OneToOneField(Turno, on_delete=models.CASCADE, related_name="atencion")
    fecha_atencion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Atención de {self.id_turno.turno} por {self.id_funcionario.nombre}"
    
class Ventanila(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    estado = models.ForeignKey(EstadoVentanilla, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_edicion = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.estado.nombre}"
    
class Puesto(models.Model):
    id_funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="puestos")
    id_ventanilla = models.ForeignKey(Ventanila, on_delete=models.CASCADE, related_name="puestos")
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.id_funcionario.nombre} - {self.id_ventanilla.nombre}"
    