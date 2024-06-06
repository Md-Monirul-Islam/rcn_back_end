from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Vendor(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    address = models.CharField(max_length=200,null=True,blank=True)

    def __str__(self):
        return self.user.username



class ProductCategory(models.Model):
    title = models.CharField(max_length=255)
    detail = models.TextField(blank=True,null=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Product Categories"
    

class Product(models.Model):
    category = models.ForeignKey(ProductCategory,on_delete=models.SET_NULL,null=True,related_name='category_product')
    vendor = models.ForeignKey(Vendor,on_delete=models.SET_NULL,null=True)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255,unique=True,null=True)
    detail = models.TextField(null=True,blank=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    usd_price = models.DecimalField(max_digits=10,decimal_places=2,default=114)
    tags = models.TextField(null=True)
    image = models.ImageField(upload_to='product_images',null=True)
    demo_url = models.URLField(null=True,blank=True)
    product_file = models.FileField(upload_to='product_files/',null=True)
    downloads = models.IntegerField(max_length=200,null=True,default=0)
    def __str__(self):
        return self.title
    
    def tag_list(self):
        if self.tags:
            return self.tags.split(',')
        else:
            return []
        


class Customer(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    phone = models.PositiveBigIntegerField(unique=True)

    def __str__(self):
        return self.user.username
    

class Order(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='customer_order')
    order_time = models.DateTimeField(auto_now_add=True)
    order_status = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    def __str__(self):
        return f"Order #{self.pk} - {str(self.order_time)}"



class OrderItems(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    def __str__(self):
        return self.product.title
    
    class Meta:
        verbose_name_plural = 'Order Items'


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='customer_address')
    address = models.TextField()
    default_address = models.BooleanField(default=False)

    def __str__(self):
        return self.address
    
    class Meta:
        verbose_name_plural = 'Customer Addresses'



class ProductRating(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='rating_customers')
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product_ratings')
    rating = models.IntegerField()
    reviews = models.TextField()
    add_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.rating} - {self.reviews}'
    



class ProductImage(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product_image')
    image = models.ImageField(upload_to='product_images',blank=True,null=True)

    def __str__(self):
        return self.image.url
    


class WishList(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.title} - {self.customer.user.first_name}"

