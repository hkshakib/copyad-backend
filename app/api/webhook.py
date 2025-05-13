from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings
from app.core.supabase_client import supabase
import stripe

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

PRICE_TO_PLAN = {
    "price_1RO5vjQY1povsxIx45qftUtb": "pro",         # monthly
    "price_1RO5wDQY1povsxIx4s4cvYOR": "pro",         # yearly
    "price_1RO5wXQY1povsxIxa0nDVThh": "enterprise",  # monthly
    "price_1RO5woQY1povsxIxBC33fSKD": "enterprise"   # yearly
}

@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]

        print("✅ Handling checkout.session.completed")
        print("📦 Session ID:", session_id)

        # Retrieve full session with line items
        full_session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["line_items"]
        )

        # ✅ Get user ID from session
        user_id = full_session.get("client_reference_id")
        customer_email = full_session.get("customer_email") or \
                         full_session.get("customer_details", {}).get("email")

        line_items = full_session.get("line_items", {}).get("data", [])
        price_id = line_items[0]["price"]["id"] if line_items else None
        plan_name = PRICE_TO_PLAN.get(price_id)

        print("🆔 Supabase UID:", user_id)
        print("📧 Email:", customer_email)
        print("💳 Price ID:", price_id)
        print("🧾 Plan to assign:", plan_name)

        if not user_id:
            print("❌ Missing Supabase user ID (client_reference_id)")
            return {"status": "missing_user_id"}

        if not plan_name:
            print("❌ Unknown price ID")
            return {"status": "unhandled_price"}

        # ✅ Check if user_profile row exists for user_id
        # existing = supabase.table("user_profile").select("*").eq("id", user_id).execute()

        response = supabase.table("user_profile").upsert({
            "id": user_id,
            "email": customer_email,
            "plan": plan_name
        }).execute()

        print("✅ Supabase response:", response)

    return {"status": "success"}
