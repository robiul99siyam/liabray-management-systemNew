from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, View
from .models import Transcation
from .forms import TranscationForm,reviewForm
from .constant import DEPOSIT, BORROW_BOOK
from post.models import PostModel
from django.shortcuts import render, redirect, get_object_or_404
from .models import BorrowedBookModel
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from user_account.views import send_email

#--------------------------- TransactionCreateMixi ---------------------->
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = "deposit.html"
    model = Transcation
    title = ""
    success_url = reverse_lazy("home")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"account": self.request.user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title})

        return context


#--------------------------send email funciton --------------------------->
def d_send_email(user,template,subject,amount):
    message = render_to_string(template,{
        'user':user,
            'amount':amount,
        })
    send_mail = EmailMultiAlternatives(subject,"",to=[user.email])
    send_mail.attach_alternative(message,'text/html')
    send_mail.send()
#--------------------------- DepositMoneyView ---------------------->
class DepositMoneyView(TransactionCreateMixin):
    form_class = TranscationForm
    title = "Deposit Form"

    def get_initial(self):
        initial = {"transaction_type": DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        account = self.request.user.account
        account.balance += amount
        account.save(update_fields=["balance"])

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully',
        )

        d_send_email(self.request.user,'d.html','Deposite Book Shop',amount)
        return super().form_valid(form)




#--------------------------- BorrowBook ---------------------->
def BorrowBook(request, id):
    book = get_object_or_404(PostModel, pk=id)

    user_balance = int(request.user.account.balance)
    book_price = int(book.borrowed_price)

    if user_balance >= book_price:
        BorrowedBookModel.objects.create(user=request.user, book=book)

        request.user.account.balance -= book_price
        request.user.account.save()
        messages.success(request, "Borrow Book Successfully Now !")
        send_email(request.user, "borrow.html", "Borrow A book in Book Shop")
    return redirect("home")



#--------------------------- returnBook ---------------------->
def returnBook(request, id):
    borrowed_book = get_object_or_404(BorrowedBookModel, pk=id, user=request.user)
    book_price = int(borrowed_book.book.borrowed_price)
    request.user.account.balance += book_price
    request.user.account.save()
    borrowed_book.delete()
    messages.success(request, "Book returned successfully!")
    send_email(request.user, 'return.html', 'Returned a book in Book Shop')
    return redirect("home")




#--------------------------- TransacationReport ---------------------->
class TransacationReport(LoginRequiredMixin, ListView):
    template_name = "transaction.html"
    model = Transcation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"account": self.request.user.account})
        context["transcation"] = Transcation.objects.filter(
            account=self.request.user.account
        )

        return context



