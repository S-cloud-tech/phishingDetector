from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from .models import *
from .gmail_client import GmailClient
from .link_analyzer import LinkAnalyzer
from .ai_detector import AITextDetector
import os
import traceback
from email.utils import parsedate_to_datetime


def landing_page(request):
    # Landing page for non-authenticated users.
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')


@require_http_methods(["GET", "POST"])
def register_view(request):
    # User registration
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, 'All fields are required.')
            return render(request, 'auth/signup.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/signup.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'auth/signup.html')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/signup.html')
        
        # Checauthisignup
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/signup.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            # Log the user in
            login(request, user)
            
            messages.success(request, f'Welcome {username}! Your account has been created.')
            return redirect('connect_gmail')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'auth/signup.html')
    
    return render(request, 'auth/signup.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    # User login view.
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'detector/login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', 'dashboard')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'auth/login.html')
    
    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    # User logout view.
    username = request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {username}! You have been logged out.')
    return redirect('landing')


@login_required
def delete_account(request):
    # Delete user account
    if request.method != "POST":
        return HttpResponse(status=405)  # Only allow POST

    user = request.user

    try:
        # Delete related Gmail account
        GmailAccount.objects.filter(user=user).delete()

        # Delete all system-related data
        EmailMessage.objects.filter(gmail_account__user=user).delete()
        ScanHistory.objects.filter(gmail_account__user=user).delete()

        # Log user out
        logout(request)

        # Delete user account last
        user.delete()

        messages.success(request, "Your account has been permanently deleted.")
        return redirect('login')  # After account is deleted, you're redirected to login page

    except Exception as e:
        messages.error(request, f"Error deleting account: {str(e)}")
        return redirect('dashboard')


@login_required
def profile_view(request):
    # View User profile
    from .models import GmailAccount, EmailMessage
    
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        
        # Get user statistics
        total_emails = EmailMessage.objects.filter(
            gmail_account=gmail_account
        ).count()
        
        safe_emails = EmailMessage.objects.filter(
            gmail_account=gmail_account,
            risk_level='SAFE'
        ).count()
        
        phishing_emails = EmailMessage.objects.filter(
            gmail_account=gmail_account,
            is_phishing=True
        ).count()
        
        context = {
            'gmail_account': gmail_account,
            'total_emails': total_emails,
            'safe_emails': safe_emails,
            'phishing_emails': phishing_emails
        }
    except GmailAccount.DoesNotExist:
        context = {'gmail_account': None}
    
    return render(request, 'profile/profile.html', context)


@login_required
def dashboard(request):
    # Authenticated User dashboard
    try:
        gmail_account = GmailAccount.objects.filter(user=request.user, is_active=True).first()
        
        if gmail_account:
            # Get recent scans
            recent_scans = ScanHistory.objects.filter(
                gmail_account=gmail_account
            )[:5]
            
            # Get statistics
            total_emails = EmailMessage.objects.filter(
                gmail_account=gmail_account
            ).count()
            
            safe_emails = EmailMessage.objects.filter(
                gmail_account=gmail_account,
                risk_level='SAFE'
            ).count()
            
            phishing_emails = EmailMessage.objects.filter(
                gmail_account=gmail_account,
                is_phishing=True
            ).count()
            
            ai_phishing = EmailMessage.objects.filter(
                gmail_account=gmail_account,
                is_phishing=True,
                is_ai_generated=True
            ).count()
        else:
            # Gmail inactive or not connected
            recent_scans = []
            total_emails = safe_emails = phishing_emails = ai_phishing = 0
        
        context = {
            'gmail_account': gmail_account,
            'recent_scans': recent_scans,
            'stats': {
                'total': total_emails,
                'safe': safe_emails,
                'phishing': phishing_emails,
                'ai_phishing': ai_phishing
            }
        }
        
    except GmailAccount.DoesNotExist:
        context = {'gmail_account': None}
    
    return render(request, 'detector/dashboard.html', context)


@login_required
def connect_gmail(request):
    # Connect Gmail account using OAuth.
    if request.method == 'POST':
        try:
            client = GmailClient()
            
            # Pass user ID for user-specific token
            if client.authenticate(user_id=request.user.id):
                # Get user's email
                service = client.service
                profile = service.users().getProfile(userId='me').execute()
                email_address = profile['emailAddress']
                
                # Save or update Gmail account
                gmail_account, created = GmailAccount.objects.get_or_create(
                    user=request.user,
                    defaults={'email': email_address}
                )
                
                if not created:
                    gmail_account.email = email_address
                    gmail_account.is_active = True
                    gmail_account.save()
                
                messages.success(request, f'Successfully connected {email_address}')
                return redirect('dashboard')
            else:
                messages.error(request, 'Failed to authenticate Gmail account')
                
        except Exception as e:
            messages.error(request, f'Error connecting Gmail: {str(e)}')
    
    return render(request, 'detector/connect_gmail.html')


@login_required
def disconnect_gmail(request):
    # Disconnect gmail
    if request.method != "POST":
        return HttpResponse(status=405)  # Only POST method will be allowed

    user = request.user

    try:
        gmail_account = GmailAccount.objects.filter(user=request.user).first()

        if not gmail_account:
            messages.error(request, "No connected Gmail account found.")
            return redirect('dashboard')

        # Delete the token.pickle file to avoid login back into the same gmail once you 
        token_path = f"token_{request.user.id}.pickle"
        
        if os.path.exists(token_path):
            os.remove(token_path)
        else:
            print(f"Token file not found: {token_path}")

        EmailMessage.objects.filter(gmail_account__user=user).delete()
        ScanHistory.objects.filter(gmail_account__user=user).delete()

        # Deactivate the account
        gmail_account.is_active = False
        gmail_account.token_file = None
        gmail_account.last_sync = None

        gmail_account.save()

        messages.success(request, f"Gmail account {gmail_account.email} disconnected.")
        return redirect('dashboard')

    except Exception as e:
        messages.error(request, f"Error disconnecting Gmail: {str(e)}")
        return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def start_scan(request):
    # Start scanning Gmail inbox.
    try:
        # Check if Gmail account exists
        try:
            gmail_account = GmailAccount.objects.get(user=request.user)
        except GmailAccount.DoesNotExist:
            return JsonResponse({
                'error': 'Gmail account not connected. Please connect your Gmail first.'
            }, status=400)
        
        # Create scan history record
        scan = ScanHistory.objects.create(
            gmail_account=gmail_account,
            status='RUNNING'
        )
        
        # Initialize analyzers
        try:
            gmail_client = GmailClient()
            link_analyzer = LinkAnalyzer()
            ai_detector = AITextDetector()
        except Exception as e:
            scan.status = 'FAILED'
            scan.error_message = f'Failed to initialize analyzers: {str(e)}'
            scan.save()
            return JsonResponse({'error': f'Initialization error: {str(e)}'}, status=500)
        
        # Authenticate with Gmail
        try:
            if not gmail_client.authenticate(user_id=request.user.id):
                scan.status = 'FAILED'
                scan.error_message = 'Failed to authenticate with Gmail'
                scan.save()
                return JsonResponse({'error': 'Gmail authentication failed'}, status=400)
        except Exception as e:
            scan.status = 'FAILED'
            scan.error_message = f'Authentication error: {str(e)}'
            scan.save()
            return JsonResponse({'error': f'Authentication error: {str(e)}'}, status=500)
        
        # Scan emails
        try:
            max_emails = int(request.POST.get('max_emails', 50))
            emails = gmail_client.scan_inbox(max_results=max_emails)
        except Exception as e:
            scan.status = 'FAILED'
            scan.error_message = f'Error scanning inbox: {str(e)}'
            scan.save()
            return JsonResponse({'error': f'Scan error: {str(e)}'}, status=500)
        
        safe_count = 0
        phishing_count = 0
        ai_phishing_count = 0
        processed_count = 0  # Track actually processed emails
        
        for email_data in emails:
            try:
                # Parse the date properly
                try:
                    received_date = parsedate_to_datetime(email_data['date'])
                except:
                    # Fallback to current time if date parsing fails
                    received_date = timezone.now()
                
                # Save email
                email_obj, created = EmailMessage.objects.get_or_create(
                    gmail_account=gmail_account,
                    message_id=email_data['id'],
                    defaults={
                        'subject': email_data['subject'],
                        'sender': email_data['sender'],
                        'received_date': received_date,
                        'body_text': email_data['body'],
                        'snippet': email_data['snippet']
                    }
                )
                
                # If email already exists, update its content
                if not created:
                    email_obj.subject = email_data['subject']
                    email_obj.sender = email_data['sender']
                    email_obj.received_date = received_date
                    email_obj.body_text = email_data['body']
                    email_obj.snippet = email_data['snippet']
                
                processed_count += 1  # Count this as processed
            
                # Analyze links (always re-analyze, even for existing emails)
                try:
                    # Delete old link analyses for this email if re-scanning
                    if not created:
                        LinkAnalysis.objects.filter(email=email_obj).delete()
                    
                    link_results = link_analyzer.analyze_multiple_links(email_data['links'])
                    max_risk_score = 0
                    is_phishing = False
                    
                    for link_result in link_results:
                        LinkAnalysis.objects.create(
                            email=email_obj,
                            url=link_result['url'],
                            is_suspicious=link_result['is_suspicious'],
                            risk_score=link_result['risk_score'],
                            risk_level=link_analyzer.get_risk_level(link_result['risk_score']),
                            indicators=link_result['indicators'],
                            details=link_result['details']
                        )
                        
                        if link_result['risk_score'] > max_risk_score:
                            max_risk_score = link_result['risk_score']
                        
                        if link_result['is_suspicious']:
                            is_phishing = True
                except Exception as e:
                    print(f"Link analysis error: {str(e)}")
                    is_phishing = False
                    max_risk_score = 0
                
                # Detect AI-generated text (always re-analyze)
                try:
                    # Delete old AI detection for this email if re-scanning
                    if not created:
                        AIDetectionResult.objects.filter(email=email_obj).delete()
                    
                    ai_result = ai_detector.detect(email_data['body'])
                    
                    AIDetectionResult.objects.create(
                        email=email_obj,
                        is_ai_generated=ai_result['is_ai_generated'],
                        confidence_score=ai_result['confidence'],
                        confidence_level=ai_detector.get_confidence_level(
                            ai_result['confidence']
                        ),
                        perplexity_score=ai_result['scores'].get('perplexity', 0),
                        burstiness_score=ai_result['scores'].get('burstiness', 0),
                        pattern_score=ai_result['scores'].get('pattern_match', 0),
                        uniformity_score=ai_result['scores'].get('uniformity', 0),
                        indicators=ai_result['indicators']
                    )
                except Exception as e:
                    print(f"AI detection error: {str(e)}")
                    ai_result = {'is_ai_generated': False, 'confidence': 0}
                
                # Determine final risk level
                try:
                    email_obj.is_ai_generated = ai_result['is_ai_generated']
                    email_obj.is_phishing = is_phishing
                    
                    if is_phishing and ai_result['is_ai_generated']:
                        email_obj.risk_level = 'CRITICAL'
                        ai_phishing_count += 1
                    elif is_phishing:
                        email_obj.risk_level = link_analyzer.get_risk_level(max_risk_score)
                        phishing_count += 1
                    else:
                        email_obj.risk_level = 'SAFE'
                        safe_count += 1
                    
                    email_obj.save()
                except Exception as e:
                    print(f"Error saving email classification: {str(e)}")
                    continue
            except Exception as e:
                print(f"Woow {str(e)}")
                continue
            
        # Update scan history
        scan.completed_at = timezone.now()
        scan.total_emails = processed_count
        scan.safe_emails = safe_count
        scan.phishing_emails = phishing_count
        scan.ai_generated_emails = ai_phishing_count
        scan.status = 'COMPLETED'
        scan.save()
        
        # Update statistics
        today = timezone.now().date()
        stats, _ = ThreatStatistics.objects.get_or_create(
            gmail_account=gmail_account,
            date=today
        )
        stats.total_emails_scanned = EmailMessage.objects.filter(
            gmail_account=gmail_account
        ).count()  # Total in DB, not just this scan
        stats.safe_count = EmailMessage.objects.filter(
            gmail_account=gmail_account,
            risk_level='SAFE'
        ).count()
        stats.phishing_count = EmailMessage.objects.filter(
            gmail_account=gmail_account,
            is_phishing=True
        ).count()
        stats.ai_phishing_count = EmailMessage.objects.filter(
            gmail_account=gmail_account,
            is_phishing=True,
            is_ai_generated=True
        ).count()
        stats.save()
        
        gmail_account.last_sync = timezone.now()
        gmail_account.save()
        
        return JsonResponse({
            'success': True,
            'scan_id': scan.id,
            'stats': {
                'total': processed_count,
                'safe': safe_count,
                'phishing': phishing_count,
                'ai_phishing': ai_phishing_count
            },
            'message': f'Scanned {processed_count} emails.{processed_count - len([e for e in emails if EmailMessage.objects.filter(gmail_account=gmail_account, message_id=e["id"]).exists()])} new, {len([e for e in emails if EmailMessage.objects.filter(gmail_account=gmail_account, message_id=e["id"]).exists()])} updated.'
        })     
    except Exception as e:
        # Log the full traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in start_scan: {error_trace}")
        
        # If the scan object was successfully created before the crash, mark it as FAILED
        if 'scan' in locals() and scan.status == 'RUNNING':
            scan.status = 'FAILED'
            scan.error_message = f'Unexpected error: {str(e)}'
            scan.save()
            
        return JsonResponse({
            'error': f'An unexpected server error occurred: {str(e)}',
            'details': 'Please check server logs for details.'
        }, status=500)

@login_required
def email_list(request):
    # Display list of scanned emails.
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        
        # Get filter parameters
        risk_filter = request.GET.get('risk', 'all')
        
        emails = EmailMessage.objects.filter(gmail_account=gmail_account)
        
        if risk_filter != 'all':
            if risk_filter == 'phishing':
                emails = emails.filter(is_phishing=True)
            elif risk_filter == 'ai_phishing':
                emails = emails.filter(is_phishing=True, is_ai_generated=True)
            elif risk_filter == 'safe':
                emails = emails.filter(risk_level='SAFE')
        
        context = {
            'emails': emails,
            'risk_filter': risk_filter
        }
        
    except GmailAccount.DoesNotExist:
        context = {'emails': [], 'error': 'Gmail account not connected'}
    
    return render(request, 'detector/email_list.html', context)


@login_required
def email_detail(request, email_id):
    # Display detailed analysis for a specific email.
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        email = EmailMessage.objects.get(
            id=email_id,
            gmail_account=gmail_account
        )
        
        links = LinkAnalysis.objects.filter(email=email)
        ai_detection = AIDetectionResult.objects.filter(email=email).first()
        
        context = {
            'email': email,
            'links': links,
            'ai_detection': ai_detection
        }
        
    except (GmailAccount.DoesNotExist, EmailMessage.DoesNotExist):
        context = {'error': 'Email not found'}
    
    return render(request, 'detector/email_detail.html', context)


@login_required
def debug_email_count(request):
    # Debug endpoint to check how many emails are actually in the database.
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        
        # Get all emails for this user
        all_emails = EmailMessage.objects.filter(gmail_account=gmail_account)
        
        # Get statistics
        total_count = all_emails.count()
        safe_count = all_emails.filter(risk_level='SAFE').count()
        phishing_count = all_emails.filter(is_phishing=True).count()
        ai_count = all_emails.filter(is_ai_generated=True).count()
        
        # Get recent emails
        recent_emails = all_emails.order_by('-received_date')[:10]
        
        email_list = []
        for email in recent_emails:
            email_list.append({
                'id': email.id,
                'subject': email.subject,
                'sender': email.sender,
                'date': str(email.received_date),
                'risk_level': email.risk_level,
                'is_phishing': email.is_phishing,
                'is_ai': email.is_ai_generated
            })
        
        return JsonResponse({
            'status': 'success',
            'database_stats': {
                'total_emails': total_count,
                'safe': safe_count,
                'phishing': phishing_count,
                'ai_generated': ai_count
            },
            'recent_emails': email_list,
            'message': f'Found {total_count} emails in database for user {request.user.username}'
        })
        
    except GmailAccount.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Gmail account not connected'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def debug_last_scan(request):
    # Debug endpoint to check the last scan results.
    
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        
        # Get last scan
        last_scan = ScanHistory.objects.filter(
            gmail_account=gmail_account
        ).order_by('-started_at').first()
        
        if not last_scan:
            return JsonResponse({
                'status': 'info',
                'message': 'No scans found'
            })
        
        return JsonResponse({
            'status': 'success',
            'last_scan': {
                'id': last_scan.id,
                'started': str(last_scan.started_at),
                'completed': str(last_scan.completed_at) if last_scan.completed_at else None,
                'status': last_scan.status,
                'total_emails': last_scan.total_emails,
                'safe_emails': last_scan.safe_emails,
                'phishing_emails': last_scan.phishing_emails,
                'ai_generated_emails': last_scan.ai_generated_emails,
                'error_message': last_scan.error_message
            }
        })
        
    except GmailAccount.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Gmail account not connected'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

