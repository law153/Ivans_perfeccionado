# Generated by Django 4.1.5 on 2023-05-23 15:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id_categoria', models.IntegerField(primary_key=True, serialize=False, verbose_name='De momento solo 7')),
                ('nombre_categoria', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Consulta',
            fields=[
                ('id_consulta', models.AutoField(primary_key=True, serialize=False)),
                ('nombre_consultante', models.CharField(max_length=30)),
                ('asunto_consulta', models.CharField(max_length=60)),
                ('mensaje_consulta', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Pregunta',
            fields=[
                ('id_pregunta', models.IntegerField(primary_key=True, serialize=False, verbose_name='De momento solo 1,2 y 3')),
                ('nombre_pregunta', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id_rol', models.IntegerField(primary_key=True, serialize=False, verbose_name='Solo dos posibles, 1 para cliente y 2 para admin')),
                ('nombre_rol', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id_usuario', models.AutoField(primary_key=True, serialize=False)),
                ('rut', models.IntegerField()),
                ('dvrut', models.IntegerField()),
                ('nombre', models.CharField(max_length=30)),
                ('apellido', models.CharField(max_length=30)),
                ('telefono', models.IntegerField()),
                ('correo', models.CharField(max_length=60)),
                ('clave', models.CharField(max_length=20)),
                ('direccion', models.CharField(max_length=60)),
                ('respuesta', models.CharField(max_length=50)),
                ('foto_usuario', models.ImageField(upload_to='usuarios')),
                ('pregunta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.pregunta')),
                ('rol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.rol')),
            ],
        ),
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id_venta', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_venta', models.DateField()),
                ('estado', models.CharField(max_length=30)),
                ('fecha_entrega', models.DateField()),
                ('total', models.IntegerField()),
                ('carrito', models.BooleanField(verbose_name='0 para venta y 1 para carrito')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.usuario')),
            ],
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('cod_prod', models.AutoField(primary_key=True, serialize=False)),
                ('nombre_prod', models.CharField(max_length=100)),
                ('descripcion', models.CharField(max_length=300)),
                ('precio', models.IntegerField()),
                ('stock', models.IntegerField()),
                ('foto_prod', models.ImageField(upload_to='productos')),
                ('unidad_medida', models.CharField(max_length=30)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.categoria')),
            ],
        ),
        migrations.CreateModel(
            name='Detalle',
            fields=[
                ('id_detalle', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('subtotal', models.IntegerField()),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.producto')),
                ('venta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.venta')),
            ],
        ),
    ]
