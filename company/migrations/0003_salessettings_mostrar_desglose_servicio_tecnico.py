from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0002_invoicesettings_condiciones_servicio_tecnico'),
    ]

    operations = [
        migrations.AddField(
            model_name='salessettings',
            name='mostrar_desglose_servicio_tecnico',
            field=models.BooleanField(
                default=False,
                verbose_name='Mostrar desglose de mano de obra y repuestos en facturas de Servicio Técnico',
                help_text=(
                    'Desactivado (recomendado): la factura generada al facturar una '
                    'reparación muestra un único concepto de servicio con el precio '
                    'final. Activado: se listan por separado la mano de obra y cada '
                    'repuesto utilizado, igual que en una venta normal.'
                ),
            ),
        ),
    ]
