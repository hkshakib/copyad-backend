import stripe
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.core.supabase_client import get_current_user

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/checkout")
def create_checkout_session(user=Depends(get_current_user)):
    try:
        customer_email = user.get("email") or user.get("user_metadata", {}).get("email")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email='hkshakib.cse@gmail.com',
            line_items=[{
                "price": "price_1RNDUKQY1povsxIxlwdIQn2k",  # ✅ Replace with real Stripe price ID
                "quantity": 1,
            }],
            success_url='https://localhost:5173' + "?session_id={CHECKOUT_SESSION_ID}",
            # cancel_url=settings.FRONTEND_CANCEL_URL,
        )
        return {"checkout_url": session.url}

    except Exception as e:
        print("❌ Stripe Error:", e)
        raise HTTPException(status_code=500, detail="Failed to create Stripe session")
