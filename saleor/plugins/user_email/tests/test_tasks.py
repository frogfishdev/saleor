from unittest import mock

from ....account.notifications import get_default_user_payload
from ....invoice import InvoiceEvents
from ....invoice.models import Invoice, InvoiceEvent
from ....order import OrderEvents, OrderEventsEmails
from ....order.notifications import (
    get_default_fulfillment_payload,
    get_default_order_payload,
)
from ....plugins.email_common import EmailConfig
from ....plugins.user_email.tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_fulfillment_confirmation_email_task,
    send_fulfillment_update_email_task,
    send_invoice_email_task,
    send_order_canceled_email_task,
    send_order_confirmation_email_task,
    send_order_refund_email_task,
    send_password_reset_email_task,
    send_payment_confirmation_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_account_confirmation_email_task_default_template(
    mocked_send_mail, user_email_dict_config, customer_user
):
    recipient_email = "admin@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    send_account_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_account_confirmation_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        account_confirmation_template=expected_template_str,
        account_confirmation_subject=expected_subject,
    )
    recipient_email = "admin@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": "user@example.com",
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    send_account_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_password_reset_email_task_default_template(
    mocked_send_mail, user_email_dict_config, customer_user
):
    token = "token123"
    recipient_email = "admin@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    send_password_reset_email_task(recipient_email, payload, user_email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_password_reset_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        password_reset_template=expected_template_str,
        password_reset_subject=expected_subject,
    )
    token = "token123"
    recipient_email = "admin@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    send_password_reset_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_request_email_change_email_task_default_template(
    mocked_send_mail, user_email_dict_config, customer_user
):
    token = "token123"
    recipient_email = "user@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "redirect_url": f"http://localhost:8000/redirect{token}",
        "old_email": "old.user@example.com",
        "new_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_request_email_change_email_task(
        recipient_email, payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_request_email_change_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        email_change_request_template=expected_template_str,
        email_change_request_subject=expected_subject,
    )
    token = "token123"
    recipient_email = "user@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "redirect_url": f"http://localhost:8000/redirect{token}",
        "old_email": "old.user@example.com",
        "new_email": "user@example.com",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_request_email_change_email_task(
        recipient_email, payload, user_email_dict_config
    )

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_user_change_email_notification_task_default_template(
    mocked_send_mail, user_email_dict_config, customer_user
):
    recipient_email = "user@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "old_email": "old.admin@example.com",
        "new_email": "admin@example.com",
    }

    send_user_change_email_notification_task(
        recipient_email, payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_user_change_email_notification_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        email_change_confirm_template=expected_template_str,
        email_change_confirm_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "old_email": "old.admin@example.com",
        "new_email": "admin@example.com",
    }

    send_user_change_email_notification_task(
        recipient_email, payload, user_email_dict_config
    )

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_account_delete_confirmation_email_task_default_template(
    mocked_send_mail, user_email_dict_config, customer_user
):
    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "delete_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_account_delete_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_account_delete_confirmation_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        account_delete_template=expected_template_str,
        account_delete_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "delete_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_account_delete_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_set_user_password_email_task_default_template(
    mocked_send_mail, user_email_dict_config, customer_user
):
    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_set_user_password_email_task(recipient_email, payload, user_email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_set_user_password_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        account_set_password_template=expected_template_str,
        account_set_password_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_set_user_password_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_invoice_email_task_default_template(
    mocked_send_mail, user_email_dict_config, staff_user, order,
):
    invoice = Invoice.objects.create(order=order)
    recipient_email = "user@example.com"
    payload = {
        "invoice": {
            "id": invoice.id,
            "order_id": order.id,
            "number": 999,
            "download_url": "http://localhost:8000/download",
        },
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": staff_user.id,
    }

    send_invoice_email_task(recipient_email, payload, user_email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.SENT,
        user=staff_user.id,
        invoice=invoice,
        parameters__email=recipient_email,
    ).exists()
    assert order.events.filter(
        type=OrderEvents.INVOICE_SENT,
        order=order,
        user=staff_user.id,
        parameters__email=recipient_email,
    ).exists()


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_invoice_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, staff_user, order
):
    invoice = Invoice.objects.create(order=order)
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        invoice_ready_template=expected_template_str,
        invoice_ready_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    payload = {
        "invoice": {
            "id": invoice.id,
            "number": 999,
            "order_id": order.id,
            "download_url": "http://localhost:8000/download",
        },
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": staff_user.id,
    }

    send_invoice_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.SENT,
        user=staff_user.id,
        invoice=invoice,
        parameters__email=recipient_email,
    ).exists()
    assert order.events.filter(
        type=OrderEvents.INVOICE_SENT,
        order=order,
        user=staff_user.id,
        parameters__email=recipient_email,
    ).exists()


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_order_confirmation_email_task_default_template(
    mocked_send_mail, user_email_dict_config, order
):
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_order_confirmation_email_task(recipient_email, payload, user_email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_order_confirmation_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, order
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        order_confirmation_template=expected_template_str,
        order_confirmation_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_order_confirmation_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_fulfillment_confirmation_email_task_default_template(
    mocked_send_mail, user_email_dict_config, order, fulfillment, staff_user
):
    payload = get_default_fulfillment_payload(order, fulfillment)
    payload["requester_user_id"] = staff_user.pk

    send_fulfillment_confirmation_email_task(
        payload["recipient_email"], payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called

    event_email_sent = order.events.get()
    assert event_email_sent.user == staff_user
    assert event_email_sent.parameters == {
        "email": order.user_email,
        "email_type": OrderEventsEmails.FULFILLMENT,
    }


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_fulfillment_confirmation_email_task_custom_template(
    mocked_send_email,
    user_email_dict_config,
    user_email_plugin,
    order,
    fulfillment,
    staff_user,
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        fulfillment_confirmation_template=expected_template_str,
        fulfillment_confirmation_subject=expected_subject,
    )
    payload = get_default_fulfillment_payload(order, fulfillment)
    payload["requester_user_id"] = staff_user.pk
    payload["digital_lines"] = [{"fulfillmentLine": {"id": 1}}]
    recipient_email = payload["recipient_email"]

    send_fulfillment_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )

    event_email_sent, event_digital_email_sent = order.events.all().order_by("pk")
    assert event_email_sent.user == staff_user
    assert event_email_sent.parameters == {
        "email": order.user_email,
        "email_type": OrderEventsEmails.FULFILLMENT,
    }
    assert event_digital_email_sent.user == staff_user
    assert event_digital_email_sent.parameters == {
        "email": order.user_email,
        "email_type": OrderEventsEmails.DIGITAL_LINKS,
    }


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_fulfillment_update_email_task_default_template(
    mocked_send_mail, user_email_dict_config, order, fulfillment
):
    payload = get_default_fulfillment_payload(order, fulfillment)

    send_fulfillment_update_email_task(
        payload["recipient_email"], payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_fulfillment_update_email_task_custom_template(
    mocked_send_email,
    user_email_dict_config,
    user_email_plugin,
    order,
    fulfillment,
    staff_user,
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        fulfillment_update_template=expected_template_str,
        fulfillment_update_subject=expected_subject,
    )
    payload = get_default_fulfillment_payload(order, fulfillment)
    recipient_email = payload["recipient_email"]
    send_fulfillment_update_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_payment_confirmation_email_task_default_template(
    mocked_send_mail, user_email_dict_config, order, payment_dummy
):
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "payment": {
            "created": payment_dummy.created,
            "modified": payment_dummy.modified,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_payment_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called

    event_email_sent = order.events.get()
    assert event_email_sent.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.PAYMENT,
    }


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_payment_confirmation_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, order, payment_dummy
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        payment_confirmation_template=expected_template_str,
        payment_confirmation_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "payment": {
            "created": payment_dummy.created,
            "modified": payment_dummy.modified,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    send_payment_confirmation_email_task(
        recipient_email, payload, user_email_dict_config
    )

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_order_canceled_email_task_default_template(
    mocked_send_mail, user_email_dict_config, order, staff_user
):
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": staff_user.pk,
    }

    send_order_canceled_email_task(recipient_email, payload, user_email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_order_canceled_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, order, staff_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        order_cancel_template=expected_template_str,
        order_cancel_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": staff_user.pk,
    }
    send_order_canceled_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_order_refund_email_task_default_template(
    mocked_send_mail, user_email_dict_config, order, staff_user
):
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": staff_user.pk,
    }

    send_order_refund_email_task(recipient_email, payload, user_email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called

    event_email_sent = order.events.get()
    assert event_email_sent.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_REFUND,
    }


@mock.patch("saleor.plugins.user_email.tasks.send_email")
def test_send_order_refund_email_task_custom_template(
    mocked_send_email, user_email_dict_config, user_email_plugin, order, staff_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    user_email_plugin(
        order_refund_template=expected_template_str,
        order_refund_subject=expected_subject,
    )
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(order, "http://localhost:8000/redirect"),
        "recipient_email": recipient_email,
        "amount": order.total_gross_amount,
        "currency": order.currency,
        "site_name": "Saleor",
        "domain": "localhost:8000",
        "requester_user_id": staff_user.pk,
    }
    send_order_refund_email_task(recipient_email, payload, user_email_dict_config)

    email_config = EmailConfig(**user_email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )
    event_email_sent = order.events.get()
    assert event_email_sent.parameters == {
        "email": recipient_email,
        "email_type": OrderEventsEmails.ORDER_REFUND,
    }
