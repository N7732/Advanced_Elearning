from django import forms
from courses.models import Course, Module, Lesson, Quizes
from django.forms import inlineformset_factory

class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'is_free', 'price', 'currency']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition',
                'placeholder': 'e.g. Advanced Python for Data Science'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 h-32',
                'placeholder': 'What will students learn?'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-blue-200 rounded-lg',
                'min': '0'
            }),
            'currency': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-blue-200 rounded-lg'}),
            'thumbnail': forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
        }

    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get("is_free")
        price = cleaned_data.get("price")

        if not is_free and (not price or price <= 0):
            self.add_error('price', "Paid courses must have a price greater than zero.")
        return cleaned_data

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:border-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md h-20'}),
            'order': forms.NumberInput(attrs={'class': 'w-20 px-2 py-1 border border-gray-300 rounded-md'})
        }

# --- FORMSETS (The Professional Secret) ---
# This allows you to add multiple Modules to a Course on the same page.
ModuleFormSet = inlineformset_factory(
    Course, 
    Module, 
    form=ModuleForm, 
    extra=1,      # Number of empty module slots to show by default
    can_delete=True
)

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['module', 'title', 'content', 'video_url', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'id': 'lesson_content_editor'}), # Target for a Rich Text Editor
            'video_url': forms.URLInput(attrs={'placeholder': 'https://vimeo.com/...'}),
        }