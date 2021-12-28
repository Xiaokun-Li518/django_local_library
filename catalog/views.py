from django.db.models.base import Model
from django.shortcuts import render

from .models import Book, Author, BookInstance, Genre

from django.views import generic

from catalog import models

from django.contrib.auth.mixins import LoginRequiredMixin

from catalog.forms import *

from django.urls import reverse

from django.http import HttpResponseRedirect

from django.shortcuts import get_object_or_404

import datetime

from django.contrib.auth.decorators import login_required, permission_required

# Create your views here.

def index(request):
    """View function for home page of site """
    #  Generate counts of some of the main objects 
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()


    # available books (status = 'a)
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()


    # The 'all()' is implied by default.
    num_author = Author.objects.count()

    num_genre = Genre.objects.count()

    # Number of visits to this view, as counted in the session variable 
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    # request.session.set_expiry(1000)



    context = {
        'num_books': num_books, 
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_author': num_author,
        'num_genre': num_genre,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable 
    return render(request, "catalog/index.html", context=context)

"""
Just to give you some idea of how this works, the code fragment below demonstrates how you would implement the class-based view as a function if you were not using the generic class-based detail view.

def book_detail_view(request, primary_key):
    try:
        book = Book.objects.get(pk=primary_key)
    except Book.DoesNotExist:
        raise Http404('Book does not exist')

    return render(request, 'catalog/book_detail.html', context={'book': book})
Copy to Clipboard
The view first tries to get the specific book record from the model. If this fails the view should raise an Http404 exception to indicate that the book is "not found". The final step is then, as usual, to call render() with the template name and the book data in the context parameter (as a dictionary).

Alternatively, we can use the get_object_or_404() function as a shortcut to raise an Http404 exception if the record is not found.

from django.shortcuts import get_object_or_404

def book_detail_view(request, primary_key):
    book = get_object_or_404(Book, pk=primary_key)
    return render(request, 'catalog/book_detail.html', context={'book': book})

"""

@login_required
@permission_required("catalog.can_mark_returned", raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian """
    book_instance = get_object_or_404(BookInstance, pk=pk)


    # if this is a POST request then process the Form data 
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)
        # check if the form is valid 
        if form.is_valid():
            
            # process the data in form.cleaned_data as required
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL 
            return HttpResponseRedirect(reverse('all-borrowed'))
    
    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})


    context = {
        "form": form,
        "book_instance":book_instance,
    }    

    return render(request, "catalog/book_renew_librarian.html", context)



class BookListView(generic.ListView):
    model = Book
    paginate_by = 5

#That's it! The generic view will query the database to get all records for the specified 
# model (Book) then render a template located at /locallibrary/catalog/templates/catalog/book_list.html 
# (which we will create below). Within the template you can access the list of books with the template variable 
# named object_list OR book_list (i.e. generically "the_model_name_list").

# You can add attributes to change the default behavior above. For example, 
# you can specify another template file if you need to have multiple views 
# that use this same model, or you might want to use a different template variable name if 
# book_list is not intuitive for your particular template use-case. Possibly the most useful 
# variation is to change/filter the subset of results that are returned — so instead of listing 
# all books you might list top 5 books that were read by other users.

# class BookListView(generic.ListView):
#     model = Book
#     context_object_name = 'my_book_list'   # your own name for the list as a template variable
#     queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
#     template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location



class BookDetailView(generic.DetailView):
    model = Book
    paginate_by = 5


class AuthorListView(generic.ListView):
    model= Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author    



# class BookListView(generic.ListView):
#     model = Book
#     context_object_name = 'my_book_list'   # your own name for the list as a template variable
#     queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
#     template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location    

# class BookListView(generic.ListView):
#     model = Book

#     def get_queryset(self):
#         return Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')



from django.contrib.auth.mixins import PermissionRequiredMixin

class BorrowedBooksListView(PermissionRequiredMixin, generic.ListView):
    models = BookInstance
    template_name = "catalog/bookinstance_list_allborrowed_books.html"
    paginate_by = 10
    permission_required = "catalog.can_mark_returned"
    
    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


from django.views.generic.edit import CreateView, UpdateView, DeleteView 

from django.urls import reverse_lazy

from catalog.models import Author, Book


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_birth': '11/06/2020'}
    permission_required = "catalog.can_mark_returned"

class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__' # Not recommanded (potential security issue if more fields added)    



class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('Allauthors')


class BookCreate(CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    initial = {'language': 'English'}


class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'


class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('Allbooks')    



        




