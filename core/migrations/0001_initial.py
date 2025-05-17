from django.db import migrations, models
import django.contrib.auth.models

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('user_type', models.CharField(choices=[('admin', 'Administrador'), ('consultor', 'Consultor'), ('cliente', 'Cliente')], default='cliente', max_length=10)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='core_user_groups', to='auth.Group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='core_user_permissions', to='auth.Permission')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClienteProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patrimonio_total_estimado', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('rendimentos_estimados_anuais', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='cliente_profile', to='core.User')),
            ],
        ),
        migrations.CreateModel(
            name='Holding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_holding', models.CharField(max_length=255)),
                ('data_criacao_registro', models.DateField(blank=True, null=True)),
                ('valor_patrimonio_integralizado', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('clientes', models.ManyToManyField(limit_choices_to={'user_type': 'cliente'}, related_name='holdings_participadas', to='core.User')),
                ('consultor_responsavel', models.ForeignKey(blank=True, limit_choices_to={'user_type': 'consultor'}, null=True, on_delete=models.SET_NULL, related_name='holdings_assessoradas', to='core.User')),
            ],
        ),
        migrations.CreateModel(
            name='ProcessoHolding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_atual', models.CharField(choices=[('aguardando_documentos', 'Aguardando Documentos'), ('documentacao_em_analise', 'Documentação em Análise'), ('elaboracao_contrato', 'Elaboração de Contrato Social'), ('registro_junta', 'Registro na Junta Comercial'), ('providencias_pos_registro', 'Providências Pós-Registro'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado')], default='aguardando_documentos', max_length=30)),
                ('data_inicio_processo', models.DateTimeField(auto_now_add=True)),
                ('data_ultima_atualizacao', models.DateTimeField(auto_now=True)),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('cliente_principal', models.ForeignKey(on_delete=models.PROTECT, related_name='processos_holding', to='core.User')),
                ('consultor_designado', models.ForeignKey(blank=True, limit_choices_to={'user_type': 'consultor'}, null=True, on_delete=models.SET_NULL, related_name='processos_designados', to='core.User')),
                ('holding_associada', models.OneToOneField(blank=True, null=True, on_delete=models.SET_NULL, related_name='processo_criacao', to='core.Holding')),
            ],
        ),
        migrations.CreateModel(
            name='Documento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_documento', models.CharField(max_length=255)),
                ('arquivo', models.FileField(upload_to='documentos_holdings/%Y/%m/%d/')),
                ('categoria', models.CharField(choices=[('pessoais_socios', 'Documentos pessoais dos sócios'), ('patrimonio_incorporado', 'Documentos do patrimônio a ser incorporado'), ('societarios_registro', 'Documentos societários (Junta/Cartório)'), ('providencias_pos_registro', 'Outras providências pós-registro')], max_length=30)),
                ('data_upload', models.DateTimeField(auto_now_add=True)),
                ('descricao_adicional', models.TextField(blank=True, null=True)),
                ('valor_referencia', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('enviado_por', models.ForeignKey(limit_choices_to={'user_type': 'cliente'}, null=True, on_delete=models.SET_NULL, related_name='documentos_enviados', to='core.User')),
                ('processo_holding', models.ForeignKey(on_delete=models.CASCADE, related_name='documentos', to='core.ProcessoHolding')),
            ],
        ),
        migrations.CreateModel(
            name='AnaliseEconomia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano_referencia', models.PositiveIntegerField()),
                ('economia_tributaria_estimada', models.DecimalField(decimal_places=2, max_digits=15)),
                ('patrimonio_liquido_projetado', models.DecimalField(decimal_places=2, max_digits=15)),
                ('data_calculo', models.DateField(auto_now_add=True)),
                ('holding', models.OneToOneField(on_delete=models.CASCADE, related_name='analise_economia', to='core.Holding')),
            ],
        ),
    ]