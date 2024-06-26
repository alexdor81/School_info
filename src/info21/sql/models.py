import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint


class Peers(models.Model):
    """Информация о пирах."""

    nickname = models.CharField(
        "Ник пира", primary_key=True, db_column="Nickname", max_length=255
    )
    birthday = models.DateField("День рождения", db_column="Birthday", null=True)

    def __str__(self):
        return self.nickname

    class Meta:
        db_table = "Peers"
        verbose_name = "Пир"
        verbose_name_plural = "Пиры"


class Tasks(models.Model):
    """Информация о заданиях."""

    title = models.CharField(
        "Название задания", primary_key=True, db_column="Title", max_length=255
    )
    parent_task = models.CharField(
        "Задание, которое является условием входа",
        max_length=255,
        db_column="ParentTask",
        null=True,
        default=0,
    )
    max_xp = models.BigIntegerField(
        "Максимальное количество XP", db_column="MaxXP", null=True, default=0
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = "Tasks"
        verbose_name = "Задание"
        verbose_name_plural = "Задания"

    def check_value(self, value):
        return re.match(r"^(C|CPP|A|DO|SQL)\d_", value)

    def clean(self):
        if not self.check_value(self.title):
            raise ValidationError(
                "Задание должно быть названо в формате названий для Школы 21 "
                "(например, A5_s21_memory)!"
            )
        if not self.check_value(self.parent_task) and self.parent_task != "0":
            raise ValidationError(
                "Задание, которое является условием входа, должно быть названо"
                " в формате названий для Школы 21 (например, A5_s21_memory) "
                "или равно нулю!"
            )
        if self.max_xp < 0:
            raise ValidationError(
                "Максимальное количество XP не может быть " "отрицательным числом!"
            )


class Checks(models.Model):
    """Информация о проверках."""

    peer = models.ForeignKey(
        Peers, db_column="Peer", verbose_name="Ник пира", on_delete=models.CASCADE
    )
    task = models.ForeignKey(
        Tasks,
        db_column="Task",
        verbose_name="Название задания",
        on_delete=models.CASCADE,
    )
    date = models.DateField("Дата проверки", db_column="Date", null=True)

    def __str__(self):
        return self.task.title

    class Meta:
        db_table = "Checks"
        verbose_name = "Проверка"
        verbose_name_plural = "Проверки"
        constraints = [
            UniqueConstraint(fields=["peer", "task", "date"], name="unique_check")
        ]


class CheckStatus(models.TextChoices):
    """Статус проверки."""

    START = "Start"
    SUCCESS = "Success"
    FAILURE = "Failure"


class P2P(models.Model):
    """P2P проверки."""

    check_2p2 = models.ForeignKey(
        Checks, db_column="Check", verbose_name="Проверка", on_delete=models.CASCADE
    )
    checking_peer = models.ForeignKey(
        Peers,
        db_column="CheckingPeer",
        verbose_name="Ник проверяющего пира",
        on_delete=models.CASCADE,
    )
    state = models.CharField(
        "Статус проверки", db_column="State", max_length=10, choices=CheckStatus.choices
    )
    time = models.TimeField("Время проверки", db_column="Time", null=True)

    class Meta:
        db_table = "P2P"
        verbose_name = "P2P проверка"
        verbose_name_plural = "P2P проверки"
        constraints = [
            UniqueConstraint(
                fields=["check_2p2", "checking_peer", "state", "time"],
                name="unique_p2p",
            )
        ]


class Verter(models.Model):
    """Проверки Verter'ом."""

    check_verter = models.ForeignKey(
        Checks, db_column="Check", verbose_name="Проверка", on_delete=models.CASCADE
    )
    state = models.CharField(
        "Статус проверки Verter'ом",
        db_column="State",
        max_length=10,
        choices=CheckStatus.choices,
    )
    time = models.TimeField("Время проверки", db_column="Time", null=True)

    class Meta:
        db_table = "Verter"
        verbose_name = "Проверка Verter'ом"
        verbose_name_plural = "Проверки Verter'ом"
        constraints = [
            UniqueConstraint(
                fields=["check_verter", "state", "time"], name="unique_verter"
            )
        ]


class TransferredPoints(models.Model):
    """Переданные пир поинты при проверках."""

    checking_peer = models.ForeignKey(
        Peers,
        db_column="CheckingPeer",
        verbose_name="Ник проверяющего пира",
        on_delete=models.CASCADE,
        related_name="checking_peer",
    )
    checked_peer = models.ForeignKey(
        Peers,
        db_column="CheckedPeer",
        verbose_name="Ник проверяемого пира",
        on_delete=models.CASCADE,
        related_name="checked_peer",
    )
    points_amount = models.BigIntegerField(
        "Количество переданных поинтов", db_column="PointsAmount", null=True, default=0
    )

    class Meta:
        db_table = "TransferredPoints"
        verbose_name = "Переданный пир поинт"
        verbose_name_plural = "Переданные пир поинты"


class Friends(models.Model):
    """Таблица друзей."""

    peer1 = models.ForeignKey(
        Peers,
        verbose_name="Ник первого пира",
        db_column="Peer1",
        on_delete=models.CASCADE,
        related_name="peer1",
    )
    peer2 = models.ForeignKey(
        Peers,
        verbose_name="Ник второго пира",
        db_column="Peer2",
        on_delete=models.CASCADE,
        related_name="peer2",
    )

    class Meta:
        db_table = "Friends"
        verbose_name = "Друг"
        verbose_name_plural = "Друзья"


class Recommendations(models.Model):
    """Таблица пиров, к которым рекомендуют идти на проверку."""

    peer = models.ForeignKey(
        Peers,
        db_column="Peer",
        verbose_name="Ник пира, который рекомендует",
        on_delete=models.CASCADE,
        related_name="peer",
    )
    recommended_peer = models.ForeignKey(
        Peers,
        db_column="RecommendedPeer",
        verbose_name="Ник пира, которого рекомендуют",
        on_delete=models.CASCADE,
        related_name="recommended_peer",
    )

    class Meta:
        db_table = "Recommendations"
        verbose_name = "Рекомендация"
        verbose_name_plural = "Рекомендации"


class XP(models.Model):
    """Количество полученного XP."""

    check_xp = models.ForeignKey(
        Checks, db_column="Check", verbose_name="Проверка", on_delete=models.CASCADE
    )
    xp_amount = models.BigIntegerField(
        "Количество полученного XP", db_column="XPAmount"
    )

    class Meta:
        db_table = "XP"
        verbose_name = "XP"
        verbose_name_plural = "XP"
        constraints = [
            UniqueConstraint(fields=["check_xp", "xp_amount"], name="unique_xp")
        ]


class TimeTracking(models.Model):
    """Информация о посещениях пирами кампуса."""

    peer = models.ForeignKey(
        Peers, db_column="Peer", verbose_name="Ник пира", on_delete=models.CASCADE
    )
    date = models.DateField("Дата", db_column="Date", null=True)
    time = models.TimeField("Время", db_column="Time", null=True)
    state = models.IntegerField("Состояние (1 - пришел, 2 - вышел)", db_column="State")

    class Meta:
        db_table = "TimeTracking"
        verbose_name = "Посещение кампуса"
        verbose_name_plural = "Посещения кампуса"

    def clean(self):
        if self.state not in [1, 2]:
            raise ValidationError("Состояние может быть равно 1 или 2!")
