from django.core.management.base import BaseCommand
from django.apps import apps
import os
import subprocess
import tempfile

class Command(BaseCommand):
    help = 'Generate a GraphViz visualization of the project models'

    def handle(self, *args, **options):
        dot_file_content = self.generate_dot_content()
        
        # Создаем временный файл с dot содержимым
        with tempfile.NamedTemporaryFile('w', suffix='.dot', delete=False) as f:
            f.write(dot_file_content)
            dot_file = f.name
        
        # Создаем выходной файл png
        output_file = 'models_visualization.png'
        
        try:
            # Запускаем команду dot для создания png
            subprocess.run(['dot', '-Tpng', dot_file, '-o', output_file], check=True)
            self.stdout.write(self.style.SUCCESS(f'Model visualization created as {output_file}'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error running dot command: {e}'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('GraphViz (dot command) not found. Please install GraphViz.'))
        finally:
            # Удаляем временный файл
            os.unlink(dot_file)
    
    def generate_dot_content(self):
        # Начинаем создавать dot содержимое
        dot_content = [
            'digraph "Models" {',
            '  graph [rankdir=TB, overlap=false, splines=true, bgcolor="#ffffff"];',
            '  edge [arrowsize=0.8];',
            '  node [shape=record, fontsize=12, fontname="Helvetica", style="filled", fillcolor="#efefef"];',
            ''
        ]
        
        # Получаем все модели в проекте
        models = apps.get_models()
        
        # Группировка моделей по приложениям
        app_models = {}
        for model in models:
            app_label = model._meta.app_label
            if app_label not in app_models:
                app_models[app_label] = []
            app_models[app_label].append(model)
        
        # Создаем subgraphs для каждого приложения
        for app_label, models_list in app_models.items():
            dot_content.append(f'  subgraph cluster_{app_label} {{')
            dot_content.append(f'    label="{app_label}";')
            dot_content.append('    style="rounded,filled";')
            dot_content.append('    fillcolor="#e8e8e8";')
            
            # Добавляем узлы моделей
            for model in models_list:
                model_name = model.__name__
                fields = []
                
                # Собираем поля модели
                for field in model._meta.fields:
                    if field.is_relation:
                        rel_type = 'ForeignKey' if field.many_to_one else ('OneToOneField' if field.one_to_one else 'ManyToManyField')
                        fields.append(f"{field.name} : {rel_type}")
                    else:
                        fields.append(f"{field.name} : {field.get_internal_type()}")
                
                # Создаем узел модели с полями
                dot_content.append(f'    "{model_name}" [label="{{{{<title> {model_name}}}|{"|".join(fields)}}}"];')
            
            dot_content.append('  }')
        
        # Добавляем связи между моделями
        for model in models:
            model_name = model.__name__
            
            for field in model._meta.fields:
                if field.is_relation:
                    rel_model_name = field.related_model.__name__
                    if field.many_to_one:
                        dot_content.append(f'  "{model_name}" -> "{rel_model_name}" [label="{field.name}"];')
                    elif field.one_to_one:
                        dot_content.append(f'  "{model_name}" -> "{rel_model_name}" [label="{field.name}", arrowhead=none, arrowtail=none];')
            
            # Обрабатываем M2M поля
            for field in model._meta.many_to_many:
                rel_model_name = field.related_model.__name__
                dot_content.append(f'  "{model_name}" -> "{rel_model_name}" [label="{field.name}", dir=both, arrowhead=crow, arrowtail=crow];')
        
        dot_content.append('}')
        
        return '\n'.join(dot_content)