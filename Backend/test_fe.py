import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

SUBSCRIPTION_ID = "sub_1TfSF1G7IScNMF3Zm3vKtcYb" 

def correr_prueba():
    print(f"🔍 Buscando suscripción: {SUBSCRIPTION_ID}...\n")
    try:
        sub = stripe.Subscription.retrieve(SUBSCRIPTION_ID)
        sub_dict = sub.to_dict() if hasattr(sub, "to_dict") else dict(sub)
        
        print("--- LLAVES PRINCIPALES QUE STRIPE SÍ ENVIÓ ---")
        for key in sub_dict.keys():
            print(f"- {key}")
            
        print("\n--- OTRAS FECHAS SOSPECHOSAS ---")
        print(f"created: {sub_dict.get('created')}")
        print(f"start_date: {sub_dict.get('start_date')}")
        print(f"trial_end: {sub_dict.get('trial_end')}")
        
    except Exception as e:
        print(f"❌ Error conectando a Stripe: {e}")

if __name__ == "__main__":
    correr_prueba()