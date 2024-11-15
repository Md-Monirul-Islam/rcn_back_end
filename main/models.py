from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count,Sum

# Create your models here.
class Vendor(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=200,blank=True,null=True)
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
    hot_deal = models.BooleanField(default=False,blank=True,null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    def __str__(self):
        return self.title
    
    def tag_list(self):
        if self.tags:
            return self.tags.split(',')
        else:
            return []
    # class Meta:
    #     ordering = ('-id',)

    def get_final_price(self, coupon_code=None):
        """
        Calculate the final price of the product after applying a valid coupon.
        """
        final_price = self.price
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, product=self, is_active=True)
                if coupon.is_valid():
                    final_price -= coupon.discount_amount
                    self.discount_price = final_price  # Save the discount price in the product
                    self.save()  # Save the updated product to the database
            except Coupon.DoesNotExist:
                pass  # Invalid coupon code
        return final_price


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    product = models.ForeignKey(Product, related_name='product_coupon', on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, related_name='vendor_coupon', on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.code} - {self.discount_amount}"

    def is_valid(self):
        return self.is_active and (self.expiration_date is None or self.expiration_date > timezone.now())
    


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, related_name='specifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    feature_name = models.CharField(max_length=255)
    feature_value = models.CharField(max_length=255)
    add_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}: {self.feature_name} - {self.feature_value}"

        


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=14,null=False, blank=False, unique=True)
    profile_image = models.ImageField(upload_to='profile_image/',blank=True,null=True)

    def __str__(self):
        return self.user.username
    


Order_STATUS = (
    ('Confirm', 'Confirm'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
)
PAYMENT_METHOD_CHOICES = (
    ('Online Payment', 'Online Payment'),
    ('Cash on Delivery', 'Cash on Delivery'),
)
SELECT_COURIER = (
    ('Sundarban Courier Service (SCS)', 'Sundarban Courier Service (SCS)'),
    ('Karatoa Courier Service (KCS)', 'Karatoa Courier Service (KCS)'),
    ('Afzal parcel & courier', 'Afzal parcel & courier'),
    ('RedX', 'RedX'),
    ('eCourier', 'eCourier'),
    ('Pathao Courier', 'Pathao Courier'),
    ('Delivery Tiger', 'Delivery Tiger'),
    ('Janani Express Parcel Service', 'Janani Express Parcel Service'),
    ('Sheba Delivery', 'Sheba Delivery'),
)
class Order(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='customer_order')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_order',blank=True,null=True)
    order_time = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=200,blank=True,null=True,choices=Order_STATUS)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Online Payment')
    select_courier = models.CharField(max_length=50, choices=SELECT_COURIER,blank=True,null=True)

    def __str__(self):
        return f"Order #{self.pk} - {str(self.order_time)}"
    
    class Meta:
        ordering = ('-id',)



class OrderItems(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    order_time = models.DateTimeField(auto_now_add=True,blank=True,null=True)

    def __str__(self):
        return self.product.title
    
    class Meta:
        ordering = ('-id',)
    
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
    image = models.ImageField(upload_to='Revie&Rating',blank=True,null=True)
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
    


class SentEmail(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    # Foreign keys to relate the email to a customer and vendor
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_emails')
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_emails')

    def __str__(self):
        return f'Email to {self.recipient} from Vendor {self.vendor.username}'



