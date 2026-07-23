from datetime import datetime, timedelta, timezone
import unittest

from db import DEFAULT_PLANS
from notification_system import NotificationManager, NotificationPriority, NotificationType


class SubscriptionNotificationTests(unittest.TestCase):
    def setUp(self):
        self.manager = NotificationManager()

    def test_default_plan_prices(self):
        plan_prices = {plan["name"]: plan["price"] for plan in DEFAULT_PLANS}

        self.assertEqual(plan_prices["Weekly"], 30)
        self.assertEqual(plan_prices["Fortnightly"], 50)
        self.assertEqual(plan_prices["Monthly"], 80)

    def test_warning_notification_at_7_days(self):
        expiry = datetime.now(timezone.utc) + timedelta(days=7, minutes=5)
        new_notifications = self.manager.check_subscription_expiry(expiry, plan_name="Weekly")

        self.assertEqual(len(new_notifications), 1)
        self.assertEqual(new_notifications[0].notification_type, NotificationType.SUBSCRIPTION_EXPIRY)
        self.assertEqual(new_notifications[0].priority, NotificationPriority.WARNING)
        self.assertIn("Weekly", new_notifications[0].message)

    def test_urgent_notification_at_3_days(self):
        expiry = datetime.now(timezone.utc) + timedelta(days=3, minutes=5)
        new_notifications = self.manager.check_subscription_expiry(expiry, plan_name="Monthly")

        self.assertEqual(len(new_notifications), 1)
        self.assertEqual(new_notifications[0].notification_type, NotificationType.SUBSCRIPTION_EXPIRY)
        self.assertEqual(new_notifications[0].priority, NotificationPriority.URGENT)

    def test_critical_notification_at_1_day(self):
        expiry = datetime.now(timezone.utc) + timedelta(days=1, minutes=5)
        new_notifications = self.manager.check_subscription_expiry(expiry)

        self.assertEqual(len(new_notifications), 1)
        self.assertEqual(new_notifications[0].notification_type, NotificationType.SUBSCRIPTION_EXPIRY)
        self.assertEqual(new_notifications[0].priority, NotificationPriority.CRITICAL)

    def test_expired_notification(self):
        expiry = datetime.now(timezone.utc) - timedelta(minutes=1)
        new_notifications = self.manager.check_subscription_expiry(expiry)

        self.assertEqual(len(new_notifications), 1)
        self.assertEqual(new_notifications[0].notification_type, NotificationType.SUBSCRIPTION_EXPIRED)
        self.assertEqual(new_notifications[0].priority, NotificationPriority.CRITICAL)
        self.assertEqual(new_notifications[0].days_remaining, 0)

    def test_no_duplicate_threshold_notification(self):
        expiry = datetime.now(timezone.utc) + timedelta(days=7, minutes=5)
        first = self.manager.check_subscription_expiry(expiry)
        second = self.manager.check_subscription_expiry(expiry)

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        self.assertEqual(len(self.manager.get_notifications_by_type(NotificationType.SUBSCRIPTION_EXPIRY)), 1)

    def test_payment_notifications(self):
        self.manager.add_payment_notification(success=True, amount="50", plan_name="Weekly")
        self.manager.add_payment_notification(success=False)

        all_notifications = self.manager.get_all_notifications_dict()
        types = [n["type"] for n in all_notifications]
        self.assertIn(NotificationType.PAYMENT_SUCCESS.value, types)
        self.assertIn(NotificationType.PAYMENT_FAILED.value, types)


if __name__ == "__main__":
    unittest.main(verbosity=2)
