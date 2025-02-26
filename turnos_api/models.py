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

