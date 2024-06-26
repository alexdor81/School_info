import csv
import os
from typing import Union

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.forms import modelform_factory
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render

from .import_obj import (import_checks, import_friends, import_p2p,
                         import_peers, import_recommendations, import_tasks,
                         import_time_tracking, import_transferred_points,
                         import_verter, import_xp)


# Абстрактный метод для добавления объекта
def create_obj(request, table_name: str):
    try:
        model = apps.get_model(app_label="sql", model_name=table_name)
    except LookupError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table: ",
            str(err),
        )
        return HttpResponseNotFound("Такой таблицы не существует!")
    model_form = modelform_factory(model, exclude=[])
    form = model_form(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("sql:data_read", table=table_name)
    context = {"form": form, "title": table_name}
    return render(request, "sql/create.html", context)


# Абстрактный метод для удаления объекта
def delete_obj(request, table_name: str, obj_pk: Union[int, str]):
    try:
        model = apps.get_model(app_label="sql", model_name=table_name)
        if table_name == "Peers":
            obj = model.objects.get(nickname=obj_pk)
        elif table_name == "Tasks":
            obj = model.objects.get(title=obj_pk)
        else:
            obj = model.objects.get(id=obj_pk)
        obj.delete()
    except ObjectDoesNotExist as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "Object with this id does not exist: ",
            str(err),
        )
        return HttpResponseNotFound("Объект с таким id не существует!")
    except ValueError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "Incorrect object id format: ",
            str(err),
        )
        return HttpResponseNotFound("Некорректный формат id объекта!")
    except LookupError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table: ",
            str(err),
        )
        return HttpResponseNotFound("Такой таблицы не существует!")
    return redirect("sql:data_read", table=table_name)


# Абстрактный метод для обновления объекта
def update_obj(request, table_name: str, obj_pk: Union[int, str]):
    try:
        model = apps.get_model(app_label="sql", model_name=table_name)
        if table_name == "Peers":
            obj = model.objects.get(nickname=obj_pk)
        elif table_name == "Tasks":
            obj = model.objects.get(title=obj_pk)
        else:
            obj = model.objects.get(id=obj_pk)
        model_form = modelform_factory(model, exclude=[])
    except ObjectDoesNotExist as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "Object with this id does not exist: ",
            str(err),
        )
        return HttpResponseNotFound("Объект с таким id не существует!")
    except ValueError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "Incorrect object id format: ",
            str(err),
        )
        return HttpResponseNotFound("Некорректный формат id объекта!")
    except LookupError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table: ",
            str(err),
        )
        return HttpResponseNotFound("Такой таблицы не существует!")
    if request.method == "POST":
        form = model_form(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("sql:data_read", table=table_name)
    form = model_form(instance=obj)
    context = {"form": form, "title": table_name}
    return render(request, "sql/update.html", context)


# Абстрактный метод для экпорта данных
def export_table(request, table_name: str):
    try:
        model = apps.get_model(app_label="sql", model_name=table_name)
        data = model.objects.all()
    except LookupError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table: ",
            str(err),
        )
        return HttpResponseNotFound("Такой таблицы не существует!")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={table_name}.csv"
    writer = csv.writer(response)
    if table_name in ["Peers", "Tasks"]:
        field_names = [field.db_column for field in model._meta.fields]
    else:
        field_names = ["ID"] + [
            field.db_column for field in model._meta.fields if field.db_column
        ]
    writer.writerow(field_names)
    for row in data:
        obj = [getattr(row, field.attname) for field in model._meta.fields]
        writer.writerow(obj)
    return response


# Абстрактный метод для импорта данных
def import_table(request, table_name: str):
    import_func = {
        "Checks": import_checks,
        "Friends": import_friends,
        "P2P": import_p2p,
        "Peers": import_peers,
        "Recommendations": import_recommendations,
        "Tasks": import_tasks,
        "TimeTracking": import_time_tracking,
        "TransferredPoints": import_transferred_points,
        "Verter": import_verter,
        "XP": import_xp,
    }
    func = import_func.get(table_name)
    if func:
        func()
        return redirect("sql:data_read", table=table_name)
    else:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table!",
        )
        return HttpResponseNotFound("Такой таблицы не существует!")


# Абстрактный метод для удаления таблиц
def delete_table(request, table_name: str):
    try:
        model = apps.get_model(app_label="sql", model_name=table_name)
        model.objects.all().delete()
    except LookupError as err:
        request.logger.warning(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table: ",
            str(err),
        )
        return HttpResponseNotFound("Такой таблицы не существует!")
    return redirect("sql:data_read", table=table_name)


# Абстрактный метод для получения verbose_name полей модели
def get_verbose_names(model):
    verbose_names = []
    for field in model._meta.fields:
        verbose_names.append(field.verbose_name)
    return verbose_names


# Получаем список процедур и функций из БД
def get_list_proc():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            CASE
            WHEN pg_get_function_result(p.oid) IS NULL THEN 'PROCEDURE'
            ELSE 'FUNCTION'
            END AS type,
            proname AS procedure_function_name,
            pg_get_function_identity_arguments(p.oid) AS parameters,
            pg_get_function_result(p.oid) AS return_type
            FROM
            pg_proc p
            LEFT JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE
            n.nspname = 'public'
            AND (
            pg_get_function_result(p.oid) != 'trigger'
            OR pg_get_function_result(p.oid) IS NULL
            );
            """
        )
        procedures = cursor.fetchall()
        column = [col[0] for col in cursor.description]
        column.append("description")
        funcs = {}
        file = os.path.abspath(__file__).replace(
            os.path.basename(__file__), "../data/funcs.csv"
        )
        with open(file, "r", encoding="utf8") as f:
            for i in csv.reader(f, delimiter="|"):
                funcs[i[0].lower()] = i[1]
        for i in range(len(procedures)):
            try:
                procedures[i] = [*procedures[i], str(funcs[procedures[i][1]])]
            except KeyError:
                procedures[i] = [*procedures[i], None]
        return column, procedures


# Получаем список столбцов и строк из БД
def custom_sql(query: str, to_file: bool):
    with connection.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchall()
        column = [col[0] for col in cursor.description]
        if to_file:
            file = os.path.abspath(__file__).replace(
                os.path.basename(__file__), "../data/custom_sql.csv"
            )
            with open(file, "w", encoding="utf8") as f:
                writer = csv.writer(f)
                writer.writerow(column)
                for i in row:
                    writer.writerow(i)
        return column, row


# Вызов процедуры
def call_proc(proc_name: str, params: list):
    with connection.cursor() as cursor:
        params.append("procedure_result")
        cursor.execute("BEGIN")
        cursor.execute(
            "CALL " + proc_name + "(" + "%s" + ", %s" * (len(params) - 1) + ")", params
        )
        cursor = connection.create_cursor("procedure_result")
        result = cursor.fetchall()
        column = [col[0] for col in cursor.description]
        return column, result


# Вызов функции
def call_func(func_name: str, params: list):
    with connection.cursor() as cursor:
        cursor.callproc(func_name, params)
        result = cursor.fetchall()
        column = [col[0] for col in cursor.description]
        return column, result
