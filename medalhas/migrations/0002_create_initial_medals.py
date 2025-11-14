from django.db import migrations


def create_medals(apps, schema_editor):
    Medal = apps.get_model('medalhas', 'Medal')
    medals = [
        {'name': 'Primeiro Treino', 'slug': 'primeiro-treino', 'description': 'Concluiu o primeiro treino', 'threshold': 1},
        {'name': '3 Treinos', 'slug': '3-treinos', 'description': 'Concluiu 3 treinos', 'threshold': 3},
        {'name': '100 Treinos', 'slug': '100-treinos', 'description': 'Concluiu 100 treinos', 'threshold': 100},
    ]
    for m in medals:
        Medal.objects.update_or_create(slug=m['slug'], defaults=m)


class Migration(migrations.Migration):

    dependencies = [
        ('medalhas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_medals, reverse_code=migrations.RunPython.noop),
    ]
