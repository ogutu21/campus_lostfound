from django.shortcuts import render


def how_it_works(request):
    """A plain explainer page. Anyone can read it, signed in or not."""
    return render(request, "items/how_it_works.html")