from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from apps.customer.models import Profile
from apps.merchant.models import LoyaltyPendingBonus, Referral, LoyaltyCard
from datetime import date, timedelta


def loyalty_customer_list(request):
    # 1. Qidiruv so'rovini olish
    query = request.GET.get('q', '')

    # 2. Querysetni boshlash
    profiles = Profile.objects.select_related('loyalty_card').all()

    # 3. Agar qidiruv so'rovi bo'lsa, ism bo'yicha filtrlash
    if query:
        profiles = profiles.filter(full_name__icontains=query)

    context = {
        'profiles': profiles,
        'query': query  # Qidiruv maydonida so'z qolishi uchun
    }

    return render(request, 'loyalty_card/customer-list.html', context)


def loyalty_customer_detail(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    loyalty_card = getattr(profile, 'loyalty_card', None)
    pending_bonuses = LoyaltyPendingBonus.objects.filter(profile=profile).order_by('-created_at')
    referrals = Referral.objects.filter(referrer=profile).order_by('-created_at')

    context = {
        'profile': profile,
        'loyalty_card': loyalty_card,
        'pending_bonuses': pending_bonuses,
        'referrals': referrals,
    }
    # DIQQAT: Rasmingizda fayl nomi 'customers.html' edi, shuni to'g'irladim:
    return render(request, 'loyalty_card/customers.html', context)


def approve_bonus(request, bonus_id):
    if request.method == "POST":
        bonus = get_object_or_404(LoyaltyPendingBonus, id=bonus_id)

        # HTML-dagi inputdan foizni olamiz
        percent_from_admin = request.POST.get('percent')

        if bonus.status == "pending" and percent_from_admin:
            with transaction.atomic():
                bonus.status = "approved"
                bonus.percent = int(percent_from_admin)  # Admin kiritgan foiz

                # save() chaqirilganda modeldagi mantiq bonus_amountni hisoblaydi
                bonus.save()

                # LoyaltyCard balansini yangilash
                card, created = LoyaltyCard.objects.get_or_create(
                    profile=bonus.profile,
                    defaults={
                        'cycle_start': date.today(),
                        'cycle_end': date.today() + timedelta(days=60)
                    }
                )
                card.current_balance += bonus.bonus_amount
                card.save()

                messages.success(request, f"Bonus {bonus.percent}% bilan tasdiqlandi!")

    return redirect('loyalty_card/customers.html', profile_id=bonus.profile.id)


def loyalty_user_detail_view(request, profile_id):
    # 1. Profilni olish
    profile = get_object_or_404(Profile, id=profile_id)

    # 2. Loyalty Card ma'lumotlarini olish (OneToOne bo'lgani uchun getattr ishlatamiz)
    loyalty_card = getattr(profile, 'loyalty_card', None)

    # 3. Kutilayotgan bonuslar (Hamma buyurtmalar bo'yicha)
    pending_bonuses = LoyaltyPendingBonus.objects.filter(profile=profile).order_by('-created_at')

    # 4. Referallar (Bu foydalanuvchi taklif qilgan odamlar)
    referrals = Referral.objects.filter(referrer=profile).order_by('-created_at')

    # 5. Statistika hisoblash (Shablon uchun qo'shimcha)
    total_spent_on_bonuses = sum(b.order_amount for b in pending_bonuses)
    bonuses_count = pending_bonuses.count()

    context = {
        'profile': profile,
        'loyalty_card': loyalty_card,
        'pending_bonuses': pending_bonuses,
        'referrals': referrals,
        'total_spent': total_spent_on_bonuses,
        'bonuses_count': bonuses_count,
    }

    return render(request, 'loyalty_card/customers.html', context)


def edit_loyalty_card(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    # Karta borligini tekshiramiz, bo'lmasa None qaytadi
    card = getattr(profile, 'loyalty_card', None)

    if request.method == "POST":
        balance = request.POST.get('balance')
        cycle_start = request.POST.get('cycle_start')
        cycle_end = request.POST.get('cycle_end')
        cycle_number = request.POST.get('cycle_number')
        cycle_days = request.POST.get('cycle_days')

        if card:
            # Mavjud kartani yangilash
            card.current_balance = balance
            card.cycle_start = cycle_start
            card.cycle_end = cycle_end
            card.cycle_number = cycle_number
            card.cycle_days = cycle_days
            card.save()
            messages.success(request, "Loyallik kartasi muvaffaqiyatli yangilandi!")
        else:
            # Agar karta hali yo'q bo'lsa, yangi yaratish (ixtiyoriy, lekin foydali)
            from apps.merchant.models import LoyaltyCard
            LoyaltyCard.objects.create(
                profile=profile,
                current_balance=balance,
                cycle_start=cycle_start,
                cycle_end=cycle_end,
                cycle_number=cycle_number,
                cycle_days=cycle_days
            )
            messages.success(request, "Yangi loyallik kartasi yaratildi!")

        # MANA BU YERDA XATO EDI: 'loyalty_card/loyalty_edit.html' o'rniga name yozamiz
        return redirect('loyalty_customer_detail', profile_id=profile.id)

    return render(request, 'loyalty_card/loyalty_edit.html', {'profile': profile, 'card': card})


def all_pending_bonuses(request):
    query = request.GET.get('q', '')
    bonuses = LoyaltyPendingBonus.objects.all().select_related('profile', 'order')

    if query:
        bonuses = bonuses.filter(
            Q(profile__full_name__icontains=query) |
            Q(order_name__icontains=query)
        )

    return render(request, 'loyalty_card/pending_all.html', {
        'bonuses': bonuses,
        'query': query
    })


# 2. Barcha referallar ro'yxati (Search bilan)
def all_referrals(request):
    query = request.GET.get('q', '')
    referrals = Referral.objects.all().select_related('referrer', 'referee')

    if query:
        # Ham taklif qilgan, ham kelgan mijoz ismida qidiradi
        referrals = referrals.filter(
            Q(referrer__full_name__icontains=query) |
            Q(referee__full_name__icontains=query)
        )

    return render(request, 'loyalty_card/all_referrals.html', {
        'referrals': referrals,
        'query': query
    })