import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# Producto Basic
product_basic = stripe.Product.create(
    name='CliniDocs Basic',
    description='Plan básico para clínicas pequeñas'
)

price_basic_monthly = stripe.Price.create(
    product=product_basic.id,
    unit_amount=100,  # $1.00 en centavos
    currency='usd',
    recurring={'interval': 'month'}
)

price_basic_yearly = stripe.Price.create(
    product=product_basic.id,
    unit_amount=1000,  # $10.00
    currency='usd',
    recurring={'interval': 'year'}
)

# Guardar IDs en SubscriptionPlan
plan = SubscriptionPlan.objects.get(slug='basic')
plan.stripe_product_id = product_basic.id
plan.stripe_price_id_monthly = price_basic_monthly.id
plan.stripe_price_id_yearly = price_basic_yearly.id
plan.save()