from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count,Sum

# Create your models here.
class Vendor(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    phone = models.PositiveBigIntegerField(unique=True,blank=True,null=True)
    profile_image = models.ImageField(upload_to='seller_images/',blank=True,null=True)
    address = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.user.username
    
    @property
    def categories(self):
        cats = Product.objects.filter(vendor=self,category__isnull=False).values('category__title').order_by('category__title').distinct()
        return cats



class ProductCategory(models.Model):
    title = models.CharField(max_length=255)
    detail = models.TextField(blank=True,null=True)
    category_image = models.ImageField(upload_to='category_images',null=True,blank=True)

    def __str__(self):
        return self.title
     
    @property
    def total_downloads(self):
        # Order products by downloads and id, then aggregate the sum of downloads
        total = Product.objects.filter(category=self).order_by('-downloads', '-id').aggregate(total_downloads=Sum('downloads'))['total_downloads']
        return total or 0  # Return 0 if total_downloads is None
    
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
    downloads = models.IntegerField(null=True,default=0)
    publish_status = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    
    def tag_list(self):
        if self.tags:
            return self.tags.split(',')
        else:
            return []
        


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=14,null=False, blank=False, unique=True)
    profile_image = models.ImageField(upload_to='profile_image/',blank=True,null=True)

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
    
    # @property
    # def show_daily_order_report_chart(self):
    #     orders = OrderItems.objects.filter(product__vendor=self).values('order__order_time__date').annotate(Count('id'))
    #     dateList = []
    #     countList = []
    #     dataSet = {}
    #     if orders:
    #         for order in orders:
    #             dateList.append(order['order__order_time__date'])
    #             countList.append(order['id__count'])
    #             print('Orders--------->>',order)
            
    #         dataSet = {'dates':dateList,'data':countList}
    #     return dataSet
    
    # class Meta:
    #     verbose_name_plural = 'Order Items'


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='customer_address')
    address = models.TextField()
    city = models.CharField(max_length=100,null=True,blank=True)
    post = models.CharField(max_length=100,null=True,blank=True)
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
    image = models.ImageField(upload_to='multiple_product_imgs',blank=True,null=True)

    def __str__(self):
        return self.image.url
    


class WishList(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.title} - {self.customer.user.first_name}"



class Transaction(models.Model):
    TRANSACTION_STATUS = (
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='transactions',blank=True,null=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer_address = models.ForeignKey(CustomerAddress, on_delete=models.CASCADE)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    customer_postcode = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='INITIATED')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"



