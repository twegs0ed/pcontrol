from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from django.db.models import Count

from .models import ControlRecord, DimensionGroup, DimensionRecord
from .forms import ControlRecordForm


@login_required
def control_list(request):
    qs = ControlRecord.objects.select_related('controller').annotate(
        total_dimensions=Count('groups__dimensions'),
        total_details=Count('groups', distinct=True)
    ).order_by('-control_date')

    worker_filter = request.GET.get('worker', '').strip()
    if worker_filter:
        qs = qs.filter(worker__icontains=worker_filter)

    controller_filter = request.GET.get('controller', '').strip()
    if controller_filter:
        qs = qs.filter(
            controller__username__icontains=controller_filter
        )

    date_from = request.GET.get('date_from', '')
    if date_from:
        try:
            from datetime import datetime
            df = datetime.strptime(date_from, '%Y-%m-%d')
            qs = qs.filter(control_date__date__gte=df.date())
        except ValueError:
            pass

    date_to = request.GET.get('date_to', '')
    if date_to:
        try:
            from datetime import datetime
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            qs = qs.filter(control_date__date__lte=dt.date())
        except ValueError:
            pass

    if not request.user.is_superuser:
        if request.user.groups.filter(name='Контролер').exists():
            qs = qs.filter(controller=request.user)
        elif request.user.groups.filter(name='Аудитор').exists():
            pass
        else:
            qs = qs.none()

    return render(request, 'controller/control_record_list.html', {
        'records': qs,
        'worker_filter': worker_filter,
        'controller_filter': controller_filter,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def control_create(request):
    if request.method == 'POST':
        form = ControlRecordForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                record.controller = request.user
                record.save()

                # Сохраняем измерения (детали через группы)
                detail_num = 0
                while True:
                    dim_count = request.POST.get(f'detail_{detail_num}_dim_count')
                    if not dim_count or int(dim_count) == 0:
                        break

                    # Создаём группу для каждой детали
                    group = DimensionGroup.objects.create(
                        control_record=record,
                        group_number=detail_num + 1
                    )

                    for i in range(int(dim_count)):
                        value = request.POST.get(f'detail_{detail_num}_dim_{i}_value')
                        if value:  # Сохраняем только если есть значение
                            DimensionRecord.objects.create(
                                group=group,
                                detail_number=detail_num + 1,
                                dimension_number=i + 1,
                                value=value,
                                tolerance=request.POST.get(f'detail_{detail_num}_dim_{i}_tolerance', ''),
                                is_acceptable=request.POST.get(f'detail_{detail_num}_dim_{i}_acceptable') == 'on'
                            )

                    detail_num += 1

                record.calculate_rejected()
            messages.success(request, f'Запись контроля для "{record.worker}" успешно добавлена.')
            return redirect('controller:control_detail', pk=record.pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ControlRecordForm()

    return render(request, 'controller/control_record_form.html', {
        'form': form,
    })


@login_required
def control_detail(request, pk):
    record = get_object_or_404(
        ControlRecord.objects.select_related('controller').prefetch_related(
            'groups__dimensions'
        ).order_by('-control_date'),
        pk=pk
    )

    if not request.user.is_superuser:
        if request.user.groups.filter(name='Контролер').exists():
            if record.controller != request.user:
                return render(request, 'controller/access_denied.html', status=403)
        elif request.user.groups.filter(name='Аудитор').exists():
            pass
        else:
            return render(request, 'controller/access_denied.html', status=403)

    return render(request, 'controller/control_record_detail.html', {
        'record': record,
    })


@login_required
def control_edit(request, pk):
    record = get_object_or_404(
        ControlRecord.objects.select_related('controller').prefetch_related(
            'groups__dimensions'
        ),
        pk=pk
    )

    if not request.user.is_superuser:
        if request.user.groups.filter(name='Контролер').exists():
            if record.controller != request.user:
                return render(request, 'controller/access_denied.html', status=403)
        else:
            return render(request, 'controller/access_denied.html', status=403)

    if request.method == 'POST':
        form = ControlRecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            with transaction.atomic():
                record = form.save()
                # Удаляем старые группы и размеры
                record.groups.all().delete()

                # Сохраняем новые
                detail_num = 0
                while True:
                    dim_count = request.POST.get(f'detail_{detail_num}_dim_count')
                    if not dim_count or int(dim_count) == 0:
                        break

                    # Создаём группу для каждой детали
                    group = DimensionGroup.objects.create(
                        control_record=record,
                        group_number=detail_num + 1
                    )

                    for i in range(int(dim_count)):
                        value = request.POST.get(f'detail_{detail_num}_dim_{i}_value')
                        if value:  # Сохраняем только если есть значение
                            DimensionRecord.objects.create(
                                group=group,
                                detail_number=detail_num + 1,
                                dimension_number=i + 1,
                                value=value,
                                tolerance=request.POST.get(f'detail_{detail_num}_dim_{i}_tolerance', ''),
                                is_acceptable=request.POST.get(f'detail_{detail_num}_dim_{i}_acceptable') == 'on'
                            )

                    detail_num += 1

                record.calculate_rejected()
            messages.success(request, f'Запись для "{record.worker}" успешно обновлена.')
            return redirect('controller:control_detail', pk=record.pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ControlRecordForm(instance=record)

    return render(request, 'controller/control_record_form.html', {
        'form': form,
        'record': record,
    })


@login_required
def control_delete(request, pk):
    record = get_object_or_404(ControlRecord, pk=pk)

    if not request.user.is_superuser:
        return render(request, 'controller/access_denied.html', status=403)

    if request.method == 'POST':
        worker = record.worker
        record.delete()
        messages.success(request, f'Запись для "{worker}" удалена.')
        return redirect('controller:control_list')

    return render(request, 'controller/confirm_delete.html', {
        'record': record,
    })
