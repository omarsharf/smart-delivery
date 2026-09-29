import json
from datetime import datetime

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from delivery.models import Delivery, Customer, Driver

# المفتاح بيتقري من .env (عبر settings.py). لو مش موجود، المشروع شغال عادي
# والشات يرجع للردود المحلية في views.py — ومفيش أي crash وقت التشغيل.
GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", None)

STAFF = ["dispatcher", "admin"]
NOT_FOUND = {"error": "Shipment not found or access denied."}
STAFF_ONLY = {"error": "Dispatcher access required."}
CUSTOMER_ONLY = {"error": "Only customers can use this tool."}
TRANSITIONS = {
    "PENDING": ["ASSIGNED", "CANCELLED"],
    "ASSIGNED": ["IN_TRANSIT", "CANCELLED"],
    "IN_TRANSIT": ["DELIVERED", "DELAYED"],
    "DELAYED": ["IN_TRANSIT", "DELIVERED"],
}


def scoped_deliveries(user):
    if user.role == "customer":
        return Delivery.objects.filter(customer__user=user)
    if user.role == "driver":
        return Delivery.objects.filter(driver__user=user)
    if user.role in STAFF:
        return Delivery.objects.all()
    return Delivery.objects.none()


def get_shipment(user, tracking_number):
    return scoped_deliveries(user).filter(tracking_number=tracking_number).first()


def serialize_shipment(delivery):
    return {
        "tracking_number": delivery.tracking_number,
        "status": delivery.get_status_display(),
        "pickup_address": delivery.pickup_address,
        "dropoff_address": delivery.dropoff_address,
        "scheduled_date": delivery.scheduled_date.strftime("%Y-%m-%d %H:%M"),
        "created_at": delivery.created_at.strftime("%Y-%m-%d %H:%M"),
        "vehicle_type": delivery.get_vehicle_type_display()
        if delivery.vehicle_type else None,
        "driver": delivery.driver.name if delivery.driver else None,
        "notes": delivery.notes,
    }


def to_list(qs):
    return [serialize_shipment(d) for d in qs.order_by("-created_at")[:50]]


def parse_datetime(value):
    return timezone.make_aware(datetime.strptime(value, "%Y-%m-%d %H:%M"))


def set_status(delivery, new_status):
    old = delivery.status
    delivery.status = new_status
    delivery.save()
    delivery.history.create(old_status=old, new_status=new_status)


def get_shipment_info(user, tracking_number):
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    return serialize_shipment(delivery)


def get_my_shipments(user):
    if user.role != "customer":
        return CUSTOMER_ONLY
    return to_list(Delivery.objects.filter(customer__user=user))


def get_shipments_by_status(user, status):
    if user.role != "customer":
        return CUSTOMER_ONLY
    return to_list(Delivery.objects.filter(customer__user=user, status=status))


def get_tracking_history(user, tracking_number):
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    return [
        {
            "old_status": item.old_status,
            "new_status": item.get_new_status_display(),
            "changed_at": item.changed_at.strftime("%Y-%m-%d %H:%M"),
        }
        for item in delivery.history.order_by("changed_at")
    ]


def get_customer_info(user):
    if user.role != "customer":
        return CUSTOMER_ONLY
    customer = Customer.objects.filter(user=user).first()
    if not customer:
        return {"error": "Customer profile not found."}
    return {"name": customer.name, "phone": customer.phone, "address": customer.address}


def get_driver_info(user, tracking_number):
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    if not delivery.driver:
        return {"message": "No driver assigned yet."}
    return {
        "name": delivery.driver.name,
        "phone": delivery.driver.phone,
        "vehicle_type": delivery.driver.vehicle_type,
    }


def get_driver_shipments(user):
    if user.role != "driver":
        return {"error": "Only drivers can use this tool."}
    driver = Driver.objects.filter(user=user).first()
    if not driver:
        return {"error": "Driver profile not found."}
    return to_list(Delivery.objects.filter(driver=driver))


def get_pending_shipments(user):
    if user.role not in STAFF:
        return STAFF_ONLY
    shipments = Delivery.objects.filter(status="PENDING").order_by("created_at")[:50]
    return [serialize_shipment(item) for item in shipments]


def get_available_drivers(user):
    if user.role not in STAFF:
        return STAFF_ONLY
    return [
        {"name": d.name, "phone": d.phone, "vehicle_type": d.vehicle_type}
        for d in Driver.objects.filter(is_available=True)
    ]


def get_delivery_summary(user):
    if user.role != "customer":
        return CUSTOMER_ONLY
    counts = (
        Delivery.objects.filter(customer__user=user)
        .values("status")
        .annotate(total=Count("id"))
    )
    return {item["status"]: item["total"] for item in counts}


def get_delayed_deliveries(user):
    return to_list(scoped_deliveries(user).filter(status="DELAYED"))


def get_delivered_shipments(user):
    return to_list(scoped_deliveries(user).filter(status="DELIVERED"))


def search_deliveries(user, query):
    return to_list(scoped_deliveries(user).filter(
        Q(tracking_number__icontains=query)
        | Q(pickup_address__icontains=query)
        | Q(dropoff_address__icontains=query)
    ))


def filter_deliveries_by_date(user, start_date, end_date):
    return to_list(scoped_deliveries(user).filter(
        scheduled_date__date__range=(start_date, end_date)
    ))


def filter_deliveries_by_vehicle(user, vehicle_type):
    return to_list(scoped_deliveries(user).filter(vehicle_type=vehicle_type))


def filter_deliveries_by_driver(user, driver_name):
    if user.role not in STAFF:
        return STAFF_ONLY
    return to_list(Delivery.objects.filter(driver__name__icontains=driver_name))


def filter_deliveries_by_customer(user, customer_name):
    if user.role not in STAFF:
        return STAFF_ONLY
    return to_list(Delivery.objects.filter(customer__name__icontains=customer_name))


def get_all_customers(user):
    if user.role not in STAFF:
        return STAFF_ONLY
    return [
        {"name": c.name, "phone": c.phone, "address": c.address}
        for c in Customer.objects.all()[:100]
    ]


def update_customer_profile(user, name=None, phone=None, address=None):
    if user.role != "customer":
        return CUSTOMER_ONLY
    customer = Customer.objects.filter(user=user).first()
    if not customer:
        return {"error": "Customer profile not found."}
    customer.name = name or customer.name
    customer.phone = phone or customer.phone
    customer.address = address or customer.address
    customer.save()
    return {"name": customer.name, "phone": customer.phone, "address": customer.address}


def create_delivery(user, pickup_address, dropoff_address, scheduled_date,
                    vehicle_type=None, notes=""):
    if user.role != "customer":
        return CUSTOMER_ONLY
    customer = Customer.objects.filter(user=user).first()
    if not customer:
        return {"error": "Customer profile not found."}
    delivery = Delivery.objects.create(
        customer=customer,
        pickup_address=pickup_address,
        dropoff_address=dropoff_address,
        scheduled_date=parse_datetime(scheduled_date),
        vehicle_type=vehicle_type,
        notes=notes,
    )
    return serialize_shipment(delivery)


def update_delivery(user, tracking_number, **fields):
    if user.role == "driver":
        return {"error": "Drivers cannot edit deliveries."}
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    if user.role == "customer" and delivery.status != "PENDING":
        return {"error": "Only pending shipments can be edited."}
    for key in ("pickup_address", "dropoff_address", "vehicle_type", "notes"):
        if key in fields:
            setattr(delivery, key, fields[key])
    if "scheduled_date" in fields:
        delivery.scheduled_date = parse_datetime(fields["scheduled_date"])
    delivery.save()
    return serialize_shipment(delivery)


def cancel_delivery(user, tracking_number):
    if user.role == "driver":
        return {"error": "Drivers cannot cancel deliveries."}
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    if delivery.status not in ("PENDING", "ASSIGNED"):
        return {"error": "This shipment can no longer be cancelled."}
    set_status(delivery, "CANCELLED")
    return serialize_shipment(delivery)


def delete_delivery(user, tracking_number):
    if user.role != "admin":
        return {"error": "Admin access required."}
    deleted, _ = Delivery.objects.filter(tracking_number=tracking_number).delete()
    return {"message": "Shipment deleted."} if deleted else NOT_FOUND


def update_delivery_status(user, tracking_number, new_status):
    if user.role == "customer":
        return {"error": "Not allowed to update status."}
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    if new_status not in TRANSITIONS.get(delivery.status, []):
        return {"error": f"Cannot change status from {delivery.status} to {new_status}."}
    set_status(delivery, new_status)
    return serialize_shipment(delivery)


def assign_driver(user, tracking_number, driver_name):
    if user.role not in STAFF:
        return STAFF_ONLY
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    if delivery.status != "PENDING":
        return {"error": "Only pending shipments can be assigned."}
    driver = Driver.objects.filter(name__icontains=driver_name, is_available=True).first()
    if not driver:
        return {"error": "No available driver with that name."}
    delivery.driver = driver
    set_status(delivery, "ASSIGNED")
    return serialize_shipment(delivery)


def unassign_driver(user, tracking_number):
    if user.role not in STAFF:
        return STAFF_ONLY
    delivery = get_shipment(user, tracking_number)
    if not delivery:
        return NOT_FOUND
    if delivery.status != "ASSIGNED":
        return {"error": "Driver can only be removed while status is Assigned."}
    delivery.driver = None
    set_status(delivery, "PENDING")
    return serialize_shipment(delivery)


def update_driver_availability(user, is_available, driver_name=None):
    if user.role == "driver":
        driver = Driver.objects.filter(user=user).first()
    elif user.role in STAFF and driver_name:
        driver = Driver.objects.filter(name__icontains=driver_name).first()
    else:
        return {"error": "Not allowed."}
    if not driver:
        return {"error": "Driver not found."}
    driver.is_available = bool(is_available)
    driver.save()
    return {"name": driver.name, "is_available": driver.is_available}


TOOL_FUNCTIONS = {
    f.__name__: f
    for f in [
        get_shipment_info, get_my_shipments, get_shipments_by_status,
        get_tracking_history, get_customer_info, get_driver_info,
        get_driver_shipments, get_pending_shipments, get_available_drivers,
        get_delivery_summary, get_delayed_deliveries, get_delivered_shipments,
        search_deliveries, filter_deliveries_by_date, filter_deliveries_by_vehicle,
        filter_deliveries_by_driver, filter_deliveries_by_customer,
        get_all_customers, update_customer_profile, create_delivery,
        update_delivery, cancel_delivery, delete_delivery,
        update_delivery_status, assign_driver, unassign_driver,
        update_driver_availability,
    ]
}


def execute_tool(user, name, args):
    handler = TOOL_FUNCTIONS.get(name)
    if not handler:
        return {"error": "Unknown tool"}
    return handler(user, **args)


if GEMINI_API_KEY:
    # ===== وضع الذكاء الاصطناعي الكامل (لما المفتاح يبقى موجود في .env) =====
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    def decl(name, description, props=None, required=None):
        schema = {"type": "OBJECT", "properties": props or {}}
        if required:
            schema["required"] = required
        return types.FunctionDeclaration(name=name, description=description, parameters=schema)

    S = {"type": "STRING"}
    TN = {"tracking_number": S}
    DELIVERY_FIELDS = {
        "pickup_address": S,
        "dropoff_address": S,
        "scheduled_date": S,
        "vehicle_type": S,
        "notes": S,
    }
    STATUSES = ["PENDING", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "DELAYED", "CANCELLED"]

    tools = [
        types.Tool(
            function_declarations=[
                decl("get_shipment_info", "Get complete information about a shipment.", TN, ["tracking_number"]),
                decl("get_my_shipments", "Get the current customer's shipments."),
                decl("get_shipments_by_status", "Get the current customer's shipments filtered by status.",
                     {"status": {"type": "STRING", "enum": STATUSES}}, ["status"]),
                decl("get_tracking_history", "Get the status history of a shipment.", TN, ["tracking_number"]),
                decl("get_customer_info", "Get the current customer's profile information."),
                decl("get_driver_info", "Get the assigned driver's information for a shipment.", TN, ["tracking_number"]),
                decl("get_driver_shipments", "Get shipments assigned to the current driver."),
                decl("get_pending_shipments", "Get pending shipments for the dispatcher."),
                decl("get_available_drivers", "Get available drivers for the dispatcher."),
                decl("get_delivery_summary", "Get a summary of the current customer's shipment counts by status."),
                decl("get_delayed_deliveries", "Get delayed shipments."),
                decl("get_delivered_shipments", "Get completed shipments."),
                decl("search_deliveries", "Search shipments by tracking number or address.", {"query": S}, ["query"]),
                decl("filter_deliveries_by_date", "Shipments scheduled between two dates (YYYY-MM-DD).",
                     {"start_date": S, "end_date": S}, ["start_date", "end_date"]),
                decl("filter_deliveries_by_vehicle", "Shipments by vehicle type.", {"vehicle_type": S}, ["vehicle_type"]),
                decl("filter_deliveries_by_driver", "Shipments of a driver by name (staff only).",
                     {"driver_name": S}, ["driver_name"]),
                decl("filter_deliveries_by_customer", "Shipments of a customer by name (staff only).",
                     {"customer_name": S}, ["customer_name"]),
                decl("get_all_customers", "List all customers (staff only)."),
                decl("update_customer_profile", "Update the current customer's name, phone or address.",
                     {"name": S, "phone": S, "address": S}),
                decl("create_delivery", "Create a shipment. scheduled_date format: YYYY-MM-DD HH:MM.",
                     DELIVERY_FIELDS, ["pickup_address", "dropoff_address", "scheduled_date"]),
                decl("update_delivery", "Edit shipment details. scheduled_date format: YYYY-MM-DD HH:MM.",
                     {**TN, **DELIVERY_FIELDS}, ["tracking_number"]),
                decl("cancel_delivery", "Cancel a shipment if allowed.", TN, ["tracking_number"]),
                decl("delete_delivery", "Delete a shipment (admin only).", TN, ["tracking_number"]),
                decl("update_delivery_status", "Change a shipment's status.",
                     {**TN, "new_status": {"type": "STRING", "enum": STATUSES[1:]}},
                     ["tracking_number", "new_status"]),
                decl("assign_driver", "Assign an available driver to a pending shipment (staff only).",
                     {**TN, "driver_name": S}, ["tracking_number", "driver_name"]),
                decl("unassign_driver", "Remove the driver from a shipment (staff only).", TN, ["tracking_number"]),
                decl("update_driver_availability", "Set a driver's availability.",
                     {"is_available": {"type": "BOOLEAN"}, "driver_name": S}, ["is_available"]),
            ]
        )
    ]

    def run_agent(user, messages):
        contents = [
            types.Content(
                role="user" if message["role"] == "user" else "model",
                parts=[types.Part.from_text(text=message["content"])]
            )
            for message in messages
        ]

        config = types.GenerateContentConfig(
            system_instruction=(
                "You are the Smart Delivery AI assistant. "
                "Answer in the user's language. "
                "Use tools to retrieve real system data when needed. "
                "Choose tools based on the user's role and question. "
                "Never invent shipment, customer, or driver information. "
                "Never claim that an action was completed unless it was actually done. "
                "Do not reveal data belonging to other users. "
                "If a tool returns an error, explain it clearly. "
                "Do not expose internal tool names to the user. "
                "Ask the user to confirm before cancelling, deleting, or assigning. "
            ),
            tools=tools,
            temperature=0.3
        )

        for _ in range(5):
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config
            )

            candidate = response.candidates[0]
            contents.append(candidate.content)

            calls = [
                part.function_call
                for part in candidate.content.parts
                if part.function_call
            ]

            if not calls:
                return response.text or "مش قادر أجهز رد دلوقتي."

            function_responses = []

            for call in calls:
                try:
                    result = execute_tool(user, call.name, dict(call.args))
                except Exception:
                    result = {"error": "Tool execution failed."}

                if isinstance(result, list):
                    result = {"items": result}

                function_responses.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response=result
                    )
                )

            contents.append(types.Content(role="user", parts=function_responses))

        return "وصلنا للحد الأقصى من خطوات معالجة الطلب. حاول مرة تانية."

else:
    # ===== الوضع المحلي: مفيش مفتاح — المشروع شغال عادي بالردود المحلية =====
    client = None

    def run_agent(user, messages):
        # بيرجع None عشان الـ view يرجع للردود المحلية (make_reply)
        return None
