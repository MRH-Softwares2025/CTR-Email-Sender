#!/usr/bin/env python3
"""
Notification System for Subscription Expiry Alerts
Checks subscription status and generates notifications when expiry is near
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Priority levels for notifications"""
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationType(Enum):
    """Types of notifications"""
    SUBSCRIPTION_EXPIRY = "subscription_expiry"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    SYSTEM = "system"


class Notification:
    """Represents a single notification"""
    
    def __init__(self, 
                 notification_type: NotificationType,
                 title: str,
                 message: str,
                 priority: NotificationPriority = NotificationPriority.INFO,
                 expiry_date: Optional[datetime] = None,
                 days_remaining: Optional[int] = None):
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.priority = priority
        self.expiry_date = expiry_date
        self.days_remaining = days_remaining
        self.created_at = datetime.now(timezone.utc)
        self.read = False
        self.dismissed = False
    
    def to_dict(self) -> Dict:
        """Convert notification to dictionary"""
        return {
            'type': self.notification_type.value,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'days_remaining': self.days_remaining,
            'created_at': self.created_at.isoformat(),
            'read': self.read,
            'dismissed': self.dismissed
        }
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
    
    def dismiss(self):
        """Dismiss notification"""
        self.dismissed = True


class NotificationManager:
    """Manages notifications for the application"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.warning_threshold_days = 7  # Warn 7 days before expiry
        self.urgent_threshold_days = 3  # Urgent warning 3 days before expiry
        self.critical_threshold_days = 1  # Critical warning 1 day before expiry
    
    def add_notification(self, notification: Notification):
        """Add a notification to the manager"""
        self.notifications.insert(0, notification)  # Add to beginning
        logger.info(f"Notification added: {notification.title}")
    
    def get_unread_notifications(self) -> List[Notification]:
        """Get all unread notifications"""
        return [n for n in self.notifications if not n.read and not n.dismissed]
    
    def get_active_notifications(self) -> List[Notification]:
        """Get all active (not dismissed) notifications"""
        return [n for n in self.notifications if not n.dismissed]
    
    def get_notifications_by_priority(self, priority: NotificationPriority) -> List[Notification]:
        """Get notifications by priority level"""
        return [n for n in self.notifications if n.priority == priority and not n.dismissed]
    
    def dismiss_notification(self, notification_index: int):
        """Dismiss a notification by index"""
        if 0 <= notification_index < len(self.notifications):
            self.notifications[notification_index].dismiss()
    
    def dismiss_all(self):
        """Dismiss all notifications"""
        for notification in self.notifications:
            notification.dismiss()
    
    def mark_all_as_read(self):
        """Mark all notifications as read"""
        for notification in self.notifications:
            notification.mark_as_read()
    
    def clear_old_notifications(self, days: int = 30):
        """Clear notifications older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        self.notifications = [
            n for n in self.notifications 
            if n.created_at > cutoff_date or not n.dismissed
        ]
    
    def check_subscription_expiry(self, expiry_date: Optional[datetime], plan_name: Optional[str] = None) -> List[Notification]:
        """
        Check subscription expiry and generate notifications if needed
        
        Args:
            expiry_date: Subscription expiry date
            plan_name: Optional plan name for context in notifications
        
        Returns:
            List of new notifications generated
        """
        if not expiry_date:
            return []
        
        plan_info = f" ({plan_name} plan)" if plan_name else ""
        now = datetime.now(timezone.utc)
        if expiry_date <= now:
            # Subscription already expired
            notification = Notification(
                notification_type=NotificationType.SUBSCRIPTION_EXPIRED,
                title="Subscription Expired",
                message=f"Your subscription{plan_info} has expired. Please renew to continue using the service.",
                priority=NotificationPriority.CRITICAL,
                expiry_date=expiry_date,
                days_remaining=0
            )
            self.add_notification(notification)
            return [notification]
        
        days_remaining = (expiry_date - now).days
        new_notifications = []
        
        # Check if we need to generate a notification
        # Only generate if we haven't already generated one for this threshold
        existing_notifications = self.get_notifications_by_type(NotificationType.SUBSCRIPTION_EXPIRY)
        
        if days_remaining <= self.critical_threshold_days:
            if not self._has_notification_for_threshold(existing_notifications, self.critical_threshold_days):
                notification = Notification(
                    notification_type=NotificationType.SUBSCRIPTION_EXPIRY,
                    title="Subscription Expiring Soon",
                    message=f"Your subscription{plan_info} will expire in {days_remaining} day(s). Please renew to avoid service interruption.",
                    priority=NotificationPriority.CRITICAL,
                    expiry_date=expiry_date,
                    days_remaining=days_remaining
                )
                self.add_notification(notification)
                new_notifications.append(notification)
        
        elif days_remaining <= self.urgent_threshold_days:
            if not self._has_notification_for_threshold(existing_notifications, self.urgent_threshold_days):
                notification = Notification(
                    notification_type=NotificationType.SUBSCRIPTION_EXPIRY,
                    title="Subscription Expiring Soon",
                    message=f"Your subscription{plan_info} will expire in {days_remaining} day(s). Please consider renewing soon.",
                    priority=NotificationPriority.URGENT,
                    expiry_date=expiry_date,
                    days_remaining=days_remaining
                )
                self.add_notification(notification)
                new_notifications.append(notification)
        
        elif days_remaining <= self.warning_threshold_days:
            if not self._has_notification_for_threshold(existing_notifications, self.warning_threshold_days):
                notification = Notification(
                    notification_type=NotificationType.SUBSCRIPTION_EXPIRY,
                    title="Subscription Expiry Reminder",
                    message=f"Your subscription{plan_info} will expire in {days_remaining} day(s).",
                    priority=NotificationPriority.WARNING,
                    expiry_date=expiry_date,
                    days_remaining=days_remaining
                )
                self.add_notification(notification)
                new_notifications.append(notification)
        
        return new_notifications
    
    def get_notifications_by_type(self, notification_type: NotificationType) -> List[Notification]:
        """Get notifications by type"""
        return [n for n in self.notifications if n.notification_type == notification_type and not n.dismissed]
    
    def _has_notification_for_threshold(self, notifications: List[Notification], threshold_days: int) -> bool:
        """Check if there's already a notification for a specific threshold"""
        for notification in notifications:
            if notification.days_remaining == threshold_days:
                return True
        return False
    
    def add_payment_notification(self, success: bool, amount: Optional[str] = None, plan_name: Optional[str] = None):
        """Add a payment notification"""
        if success:
            plan_info = f" ({plan_name} plan)" if plan_name else ""
            notification = Notification(
                notification_type=NotificationType.PAYMENT_SUCCESS,
                title="Payment Successful",
                message=f"Your payment of KES {amount or '0'}{plan_info} was processed successfully.",
                priority=NotificationPriority.INFO
            )
        else:
            notification = Notification(
                notification_type=NotificationType.PAYMENT_FAILED,
                title="Payment Failed",
                message="Your payment could not be processed. Please try again.",
                priority=NotificationPriority.WARNING
            )
        self.add_notification(notification)
    
    def add_system_notification(self, title: str, message: str, priority: NotificationPriority = NotificationPriority.INFO):
        """Add a system notification"""
        notification = Notification(
            notification_type=NotificationType.SYSTEM,
            title=title,
            message=message,
            priority=priority
        )
        self.add_notification(notification)
    
    def get_notification_summary(self) -> Dict:
        """Get a summary of notifications"""
        unread_count = len(self.get_unread_notifications())
        urgent_count = len(self.get_notifications_by_priority(NotificationPriority.URGENT))
        critical_count = len(self.get_notifications_by_priority(NotificationPriority.CRITICAL))
        
        return {
            'total_unread': unread_count,
            'urgent_count': urgent_count,
            'critical_count': critical_count,
            'has_notifications': unread_count > 0
        }
    
    def get_all_notifications_dict(self) -> List[Dict]:
        """Get all notifications as dictionaries"""
        return [n.to_dict() for n in self.get_active_notifications()]


# Global notification manager instance
notification_manager = NotificationManager()


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance"""
    return notification_manager


def check_and_notify_subscription_expiry(expiry_date: Optional[datetime]) -> List[Notification]:
    """
    Convenience function to check subscription expiry and notify
    
    Args:
        expiry_date: Subscription expiry date
    
    Returns:
        List of new notifications generated
    """
    return notification_manager.check_subscription_expiry(expiry_date)
