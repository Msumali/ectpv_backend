from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.db.models.functions import TruncMonth
import json

from .models import CustomUser, UploadedImage


@staff_member_required
def admin_dashboard(request):
    # User stats
    user_count = CustomUser.objects.count()
    first_user = CustomUser.objects.order_by('date_joined').first()
    first_user_date = first_user.date_joined if first_user else timezone.now()

    # Active users (logged in last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_users = CustomUser.objects.filter(last_login__gte=thirty_days_ago).count()
    inactive_users = user_count - active_users

    # Image stats
    image_count = UploadedImage.objects.count()
    first_image = UploadedImage.objects.order_by('uploaded_at').first()
    first_image_date = first_image.uploaded_at if first_image else timezone.now()

    verified_count = UploadedImage.objects.filter(verified=True).count()
    unverified_count = image_count - verified_count
    verification_percentage = int((verified_count / image_count) * 100) if image_count > 0 else 0

    # Recent activity
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_activity_count = UploadedImage.objects.filter(uploaded_at__gte=seven_days_ago).count()

    # Monthly chart data
    last_n_months = timezone.now() - timedelta(days=90)
    monthly_data = (
        UploadedImage.objects
        .filter(uploaded_at__gte=last_n_months)
        .annotate(week=TruncMonth('uploaded_at'))
        .values('week')
        .annotate(count=Count('id'))
        .order_by('week')
    )

    # Debug print to verify data
    print("Monthly Upload Data:")
    for entry in monthly_data:
        print(f"Month: {entry['week']}, Count: {entry['count']}")

    # Format data for Chart.js
    chart_labels = []
    chart_data = []

    for entry in monthly_data:
        month = entry['week'].strftime('%b %y')
        chart_labels.append(month)
        chart_data.append(entry['count'])

    # If no data found, generate a default 6-month range
    if not chart_labels:
        current = timezone.now()
        for i in range(6):
            month = (current - timedelta(days=30 * i)).strftime('%b %y')
            chart_labels.insert(0, month)
            chart_data.insert(0, 0)
    else:
        # Ensure we have at least 6 months of data
        while len(chart_labels) < 6:
            # Add empty months before the earliest existing month
            earliest_month = chart_labels[0]
            earliest_datetime = timezone.datetime.strptime(earliest_month, '%b %y')
            new_month = (earliest_datetime - timedelta(days=30)).strftime('%b %y')
            chart_labels.insert(0, new_month)
            chart_data.insert(0, 0)

    context = {
        'user_count': user_count,
        'first_user_date': first_user_date,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'image_count': image_count,
        'first_image_date': first_image_date,
        'verified_count': verified_count,
        'unverified_count': unverified_count,
        'verification_percentage': verification_percentage,
        'recent_activity_count': recent_activity_count,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'admin/dashboard.html', context)