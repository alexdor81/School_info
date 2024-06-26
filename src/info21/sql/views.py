import csv
import datetime
import os
import re
from decimal import Decimal
from typing import Union

from django.apps import apps
from django.db.utils import DatabaseError, OperationalError
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render

from .forms import DynamicForm
from .utils import (call_func, call_proc, create_obj, custom_sql, delete_obj,
                    delete_table, export_table, get_list_proc,
                    get_verbose_names, import_table, update_obj)


def index(request):
    context = {
        "title": "О себе",
    }
    return render(request, "index.html", context)


def data(request):
    model_names = [
        "P2P",
        "XP",
        "Checks",
        "Friends",
        "Peers",
        "Recommendations",
        "Tasks",
        "TimeTracking",
        "TransferredPoints",
        "Verter",
    ]
    context = {"data": model_names, "title": "Данные"}
    return render(request, "sql/data.html", context)


def data_read(request, table: str):
    try:
        model = apps.get_model(app_label="sql", model_name=table)
        data = model.objects.all()
        verbose_names = get_verbose_names(model)
    except LookupError as err:
        request.logger.error(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            "There is no such table: ",
            str(err),
        )
        return HttpResponseBadRequest("Такой таблицы не существует!")
    context = {
        "data": data,
        "fields": verbose_names,
        "title": table,
    }
    return render(request, "sql/read.html", context)


def data_create(request, table: str):
    return create_obj(request, table)


def data_update(request, table: str, pk: Union[int, str]):
    return update_obj(request, table, pk)


def data_delete(request, table: str, pk: Union[int, str]):
    return delete_obj(request, table, pk)


def data_export(request, table: str):
    return export_table(request, table)


def data_import(request, table: str):
    return import_table(request, table)


def table_delete(request, table: str):
    return delete_table(request, table)


def operation(request):
    column, procedures = get_list_proc()
    context = {"title": "Операции", "column": column, "procedures": procedures}
    return render(request, "sql/operation.html", context)


def execute_sql(request):
    if request.method == "POST":
        sql_query = request.POST.get("sql_query")
        save_results = bool("save_results" in request.POST)
        try:
            columns, rows = custom_sql(sql_query, save_results)
            return render(
                request, "sql/result_sql.html", {"column": columns, "rows": rows}
            )
        except (ValueError, TypeError, OperationalError, DatabaseError) as err:
            request.logger.warning(
                "%s %s %s %s %s",
                request.method,
                request.path,
                request.META.get("REMOTE_ADDR"),
                "Error in execution custom sql query: ",
                str(err),
            )
            return render(request, "sql/result_sql.html", {"error_message": str(err)})
    else:
        return redirect("operation")


def execute_form(request, type_sql, name):
    try:
        if type_sql == "FUNCTION":
            columns, rows = call_func(name, [])
        else:
            columns, rows = call_proc(name, [])
        if "export_csv" in request.POST:
            export_csv(columns, rows, name)
        return render(
            request,
            "sql/result_sql.html",
            {"column": columns, "rows": rows, "name": name, "type": True},
        )
    except (ValueError, TypeError, OperationalError, DatabaseError) as err:
        request.logger.warning(
            "%s %s %s %s %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            f"Error in executing {type_sql}: {str(err)}",
        )
        return render(request, "sql/result_sql.html", {"error_message": str(err)})


def execute(request, type_sql, name, params):
    if re.sub(r"IN [a-zA-Z_]+ refcursor", "", params) == "":
        return execute_form(request, type_sql, name)
    form = DynamicForm(param_string=params)
    if request.method == "POST":
        form = DynamicForm(param_string=params, data=request.POST)
        if form.is_valid():
            params_list = []
            for field_name, field in form.fields.items():
                if field.widget.is_hidden and field.widget.attrs.get("refcursor", None):
                    continue
                params_list.append(form.cleaned_data[field_name])
            try:
                if type_sql == "FUNCTION":
                    columns, rows = call_func(name, params_list)
                else:
                    columns, rows = call_proc(name, params_list)
                save_session(request, columns, rows)
                return render(
                    request,
                    "sql/result_sql.html",
                    {"column": columns, "rows": rows, "name": name, "type": True},
                )
            except (ValueError, TypeError, OperationalError, DatabaseError) as err:
                request.logger.warning(
                    "%s %s %s %s %s",
                    request.method,
                    request.path,
                    request.META.get("REMOTE_ADDR"),
                    "Error in execution sql query: ",
                    str(err),
                )
                return render(
                    request, "sql/result_sql.html", {"error_message": str(err)}
                )
        else:
            if "export_csv" in request.POST:
                export_csv(
                    request.session.get("columns"), request.session.get("rows"), name
                )
                return render(
                    request,
                    "sql/result_sql.html",
                    {
                        "column": request.session.get("columns"),
                        "rows": request.session.get("rows"),
                        "name": name,
                        "type": True,
                    },
                )
            error_message = "Форма была неверной"
            request.logger.warning(
                "%s %s %s %s %s",
                request.method,
                request.path,
                request.META.get("REMOTE_ADDR"),
                "Error in executing the SQL query: incorrect form",
            )
            return render(
                request, "sql/result_sql.html", {"error_message": error_message}
            )
    return render(
        request,
        "sql/execute.html",
        {"form": form, "type": type_sql, "name": name, "name": name},
    )


def save_session(request, columns, rows):
    request.session["columns"] = columns
    new_rows = []
    for row in rows:
        new_row = []
        for value in row:
            if isinstance(value, (datetime.date, datetime.datetime)):
                new_row.append(value.strftime("%Y-%m-%d"))
            elif isinstance(value, Decimal):
                new_row.append(str(value))
            else:
                new_row.append(value)
        new_rows.append(tuple(new_row))
    request.session["rows"] = new_rows


def export_csv(columns, rows, name):
    file = (
        os.path.abspath(__file__).replace(os.path.basename(__file__), "../data/")
        + name
        + ".csv"
    )
    with open(file, "w", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
