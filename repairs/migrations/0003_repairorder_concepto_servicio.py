from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repairs', '0002_repairorder_venta'),
    ]

    operations = [
        migrations.AddField(
            model_name='repairorder',
            name='concepto_servicio',
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name='Concepto de servicio (para la factura)',
                help_text=(
                    'Descripción corta y comercial de lo que se hizo, ej. "Cambio de '
                    'pantalla OLED iPhone 13". Es el único concepto que verá el '
                    'cliente en la factura cuando el desglose de mano de obra y '
                    'repuestos está desactivado (ver Configuración de Empresa → '
                    'Ventas). Si se deja en blanco, se genera uno automáticamente '
                    'a partir del equipo.'
                ),
            ),
        ),
    ]
