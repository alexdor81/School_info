import os
from csv import reader
from datetime import datetime

from django.db import connection

from .models import (P2P, XP, Checks, Friends, Peers, Recommendations, Tasks,
                     TimeTracking, TransferredPoints, Verter)


def import_peers():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/Peers.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            Peers.objects.get_or_create(
                nickname=row[0], birthday=datetime.strptime(row[1], "%Y-%m-%d").date()
            )


def import_tasks():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/Tasks.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            Tasks.objects.get_or_create(
                title=row[0], parent_task=row[1], max_xp=int(row[2])
            )


def import_checks():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/Checks.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            Checks.objects.get_or_create(
                id=int(row[0]),
                peer=Peers.objects.get(nickname=row[1]),
                task=Tasks.objects.get(title=row[2]),
                date=datetime.strptime(row[3], "%Y-%m-%d").date(),
            )


def import_p2p():
    f = os.path.abspath(__file__).replace(os.path.basename(__file__), "../data/P2P.csv")
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            P2P.objects.get_or_create(
                id=int(row[0]),
                check_2p2=Checks.objects.get(id=row[1]),
                checking_peer=Peers.objects.get(nickname=row[2]),
                state=row[3],
                time=datetime.strptime(row[4], "%H:%M:%S").time(),
            )


def import_verter():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/Verter.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            Verter.objects.get_or_create(
                id=int(row[0]),
                check_verter=Checks.objects.get(id=row[1]),
                state=row[2],
                time=datetime.strptime(row[3], "%H:%M:%S").time(),
            )


def import_transferred_points():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/TransferredPoints.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            TransferredPoints.objects.get_or_create(
                id=int(row[0]),
                checking_peer=Peers.objects.get(nickname=row[1]),
                checked_peer=Peers.objects.get(nickname=row[2]),
                points_amount=int(row[3]),
            )


def import_friends():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/Friends.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            Friends.objects.get_or_create(
                id=int(row[0]),
                peer1=Peers.objects.get(nickname=row[1]),
                peer2=Peers.objects.get(nickname=row[2]),
            )


def import_recommendations():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/Recommendations.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            Recommendations.objects.get_or_create(
                id=int(row[0]),
                peer=Peers.objects.get(nickname=row[1]),
                recommended_peer=Peers.objects.get(nickname=row[2]),
            )


def import_xp():
    f = os.path.abspath(__file__).replace(os.path.basename(__file__), "../data/XP.csv")
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            XP.objects.get_or_create(
                id=int(row[0]),
                check_xp=Checks.objects.get(id=row[1]),
                xp_amount=int(row[2]),
            )


def import_time_tracking():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/TimeTracking.csv"
    )
    with open(f, "r", encoding="utf8") as file:
        file_reader = reader(file)
        _ = next(file_reader)
        for row in file_reader:
            TimeTracking.objects.get_or_create(
                id=int(row[0]),
                peer=Peers.objects.get(nickname=row[1]),
                date=datetime.strptime(row[2], "%Y-%m-%d").date(),
                time=datetime.strptime(row[3], "%H:%M:%S").time(),
                state=int(row[4]),
            )


def import_operations():
    f = os.path.abspath(__file__).replace(
        os.path.basename(__file__), "../data/info21.sql"
    )
    with open(f, "r", encoding="utf8") as file:
        with connection.cursor() as cursor:
            cursor.execute(file.read())
