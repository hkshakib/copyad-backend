from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.supabase_client import get_current_user
from app.core.config import settings
import stripe

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY

# 🎯 Map plan_id and plan_type to Stripe price IDs
PRICE_LOOKUP = {
    "pro": {
        "monthly": "price_1RO5vjQY1povsxIx45qftUtb",
        "yearly": "price_1RO5wDQY1povsxIx4s4cvYOR"
    },
    "enterprise": {
        "monthly": "price_1RO5wXQY1povsxIxa0nDVThh",
        "yearly": "price_1RO5woQY1povsxIxBC33fSKD"
    }
}

class CheckoutRequest(BaseModel):
    plan_id: str      # e.g. "pro"
    plan_type: str    # e.g. "monthly" or "yearly"

@router.post("/checkout")
def create_checkout_session(data: CheckoutRequest, user=Depends(get_current_user)):
    try:
        customer_email = user.email or user.user_metadata.get("email")
        price_id = PRICE_LOOKUP.get(data.plan_id, {}).get(data.plan_type)

        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid plan selection")

        session = stripe.checkout.Session.create(
            customer_email=customer_email,
            client_reference_id=user.id,  # ← Supabase UUID
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            success_url="http://localhost:5173/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:5173/cancel",
        )

        return {"checkout_url": session.url}

    except Exception as e:
        print("❌ Stripe error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to create Stripe session")
