from django.core.management.base import BaseCommand

from sql.import_obj import (import_checks, import_friends, import_operations,
                            import_p2p, import_peers, import_recommendations,
                            import_tasks, import_time_tracking,
                            import_transferred_points, import_verter,
                            import_xp)


class Command(BaseCommand):
    help = "Импорт данных из CSV-файлов в БД."

    def handle(self, *args, **options):
        try:
            import_peers()
            import_tasks()
            import_checks()
            import_p2p()
            import_verter()
            import_transferred_points()
            import_friends()
            import_recommendations()
            import_xp()
            import_time_tracking()
            import_operations()
            self.stdout.write(self.style.SUCCESS("Данные успешно загружены в БД."))
        except Exception as error:
            raise Exception("Ошибка при импорте данных:", error)
