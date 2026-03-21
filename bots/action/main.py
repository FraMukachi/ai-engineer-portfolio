import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ActionBot:
    """Bot that performs actions autonomously (bookings, orders, emails)"""
    
    def __init__(self):
        self.bookings = {}  # business_id -> bookings
        self.orders = {}    # business_id -> orders
    
    async def book_appointment(self, business_id: str, customer_name: str, 
                               date: str, time: str, service: str) -> Dict[str, Any]:
        """Book an appointment autonomously"""
        try:
            # Create booking
            booking_id = f"BOOK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            booking = {
                "id": booking_id,
                "business_id": business_id,
                "customer": customer_name,
                "date": date,
                "time": time,
                "service": service,
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }
            
            # Store booking
            if business_id not in self.bookings:
                self.bookings[business_id] = []
            self.bookings[business_id].append(booking)
            
            # Send confirmation (simulated)
            logger.info(f"Booking confirmed: {booking}")
            
            # Auto-email confirmation
            await self.send_confirmation_email(business_id, booking)
            
            return {
                "success": True,
                "booking_id": booking_id,
                "message": f"Appointment confirmed for {customer_name} on {date} at {time}",
                "details": booking
            }
            
        except Exception as e:
            logger.error(f"Booking failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def place_order(self, business_id: str, customer_name: str,
                          items: List[Dict[str, Any]], delivery_address: str) -> Dict[str, Any]:
        """Place an order autonomously"""
        try:
            # Calculate total
            total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
            
            # Create order
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            order = {
                "id": order_id,
                "business_id": business_id,
                "customer": customer_name,
                "items": items,
                "total": total,
                "delivery_address": delivery_address,
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }
            
            # Store order
            if business_id not in self.orders:
                self.orders[business_id] = []
            self.orders[business_id].append(order)
            
            # Auto-process order
            logger.info(f"Order placed: {order}")
            
            # Auto-email confirmation
            await self.send_order_confirmation(business_id, order)
            
            return {
                "success": True,
                "order_id": order_id,
                "total": total,
                "message": f"Order confirmed! Total: R{total}",
                "details": order
            }
            
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_email(self, business_id: str, to_email: str, 
                         subject: str, body: str) -> Dict[str, Any]:
        """Send email autonomously"""
        try:
            # For now, just log (will implement actual email sending)
            logger.info(f"Sending email to {to_email}: {subject}")
            
            return {
                "success": True,
                "to": to_email,
                "subject": subject,
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_confirmation_email(self, business_id: str, booking: Dict) -> None:
        """Send booking confirmation email"""
        subject = "Your Appointment Confirmation"
        body = f"""
        Dear {booking['customer']},
        
        Your appointment has been confirmed:
        Date: {booking['date']}
        Time: {booking['time']}
        Service: {booking['service']}
        
        Booking ID: {booking['id']}
        
        Thank you for choosing our service!
        """
        
        # In production, get email from business settings
        await self.send_email(business_id, "customer@example.com", subject, body)
    
    async def send_order_confirmation(self, business_id: str, order: Dict) -> None:
        """Send order confirmation email"""
        subject = "Your Order Confirmation"
        
        items_list = "\n".join([
            f"- {item.get('quantity', 1)}x {item['name']}: R{item.get('price', 0)}"
            for item in order['items']
        ])
        
        body = f"""
        Dear {order['customer']},
        
        Your order has been confirmed:
        
        Items:
        {items_list}
        
        Total: R{order['total']}
        Delivery to: {order['delivery_address']}
        
        Order ID: {order['id']}
        
        We'll notify you when your order is ready!
        """
        
        await self.send_email(business_id, "customer@example.com", subject, body)

# Singleton instance
action_bot = ActionBot()
