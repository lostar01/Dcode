from django.forms import ModelForm

class BootstrapModelForm(ModelForm):
    exclude_bootstrap = ['']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        #自定义功能
        for k,field in self.fields.items():
            if k in self.exclude_bootstrap:
                continue
            field.widget.attrs['class'] = 'form-control'