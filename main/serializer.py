import datetime
from rest_framework import serializers, generics
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Count
from .models import Product, ProductCategory, ProductImage, Transaction, Vendor,Customer,Order,OrderItems,CustomerAddress, ProductRating, WishList, Coupon




class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password']

# class UserSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=False)

#     class Meta:
#         model = User
#         fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password']



class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'address','phone','profile_image','categories']
        # depth = 1
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user, context=self.context).data
        return response


class VendorDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Vendor
        fields = ['id', 'user', 'address', 'phone', 'profile_image']

    def update(self, instance, validated_data):
        # Extract user data from validated_data
        user_data = validated_data.pop('user', None)
        
        # Update vendor fields
        instance.phone = validated_data.get('phone', instance.phone)
        instance.address = validated_data.get('address', instance.address)
        if 'profile_image' in validated_data:
            instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.save()

        # Update user fields if user data is provided
        if user_data:
            user = instance.user

            # Check if the username needs to be updated
            new_username = user_data.get('username')
            if new_username and new_username != user.username:
                # Check if the new username already exists
                if User.objects.filter(username=new_username).exists():
                    raise serializers.ValidationError({"username": "A user with that username already exists."})
                user.username = new_username

            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.email = user_data.get('email', user.email)
            if 'password' in user_data:
                user.set_password(user_data['password'])  # Update password if provided
            user.save()

        return instance




class ProductListSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tags','detail','price','usd_price','demo_url','product_ratings','image','product_file','downloads','publish_status','product_image','hot_deal']

        def __init__(self,*args, **kwargs):
            super(ProductListSerializer,self).__init__(*args, **kwargs)
        # depth = 1



class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount_amount', 'is_active', 'expiration_date', 'product',]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id','product','image']



class ProductDetailSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    product_image = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tags','detail','price','usd_price','product_ratings','product_image','demo_url','image','product_file','downloads','publish_status','hot_deal']

        def __intit__(self,*args, **kwargs):
            super(ProductDetailSerializer,self).__init__(*args, **kwargs)
        # depth = 1




class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    orders = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'profile_image', 'phone','orders']

    def get_orders(self, customer):
        # Get all OrderItems related to this customer and include order details
        order_items = OrderItems.objects.filter(order__customer=customer).select_related('order')
        return OrderItemSerializer(order_items, many=True).data

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_instance = instance.user
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()

        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()

        return instance

class CustomerDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # depth = 1



class OrderItemSerializer(serializers.ModelSerializer):
    order_status = serializers.CharField(source='order.order_status', read_only=True)
    select_courier = serializers.CharField(source='order.select_courier', read_only=True)
    order = serializers.PrimaryKeyRelatedField(read_only=True)  # Ensure order is serialized as its primary key
    
    class Meta:
        model = OrderItems
        fields = '__all__'

    def get_customer_address(self, customer):
        # Optionally, you could filter to get only the default address
        address = customer.customer_address.filter(default_address=True).first()
        if address:
            return {
                'address': address.address,
                'city': address.city,
                'post': address.post,
            }
        return None

    def to_representation(self, instance):
        response = super().to_representation(instance)
        # Serialize product details
        response['product'] = ProductDetailSerializer(instance.product, context=self.context).data
        customer = instance.order.customer
        # Serialize customer details from the order
        response['customer'] = {
            'customer_id': instance.order.customer.user.id,
            'first_name': instance.order.customer.user.first_name,
            'last_name': instance.order.customer.user.last_name,
            'email': instance.order.customer.user.email,
            'phone': instance.order.customer.phone,
            'address': self.get_customer_address(customer),
        }
        return response


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['status']


class OrderSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'order_time', 'order_status', 'total_amount', 'transactions', 'payment_method', 'order_items','select_courier']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        # Serializing customer details explicitly
        response['customer'] = {
            'customer_id': instance.customer.user.id,
            'first_name': instance.customer.user.first_name,
            'last_name': instance.customer.user.last_name,
            'email': instance.customer.user.email,
            'phone': instance.customer.phone,
        }
        return response



# class TransactionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = ['status']

# class OrderSerializer(serializers.ModelSerializer):
#     transactions = TransactionSerializer(many=True)

#     class Meta:
#         model = Order
#         fields = ['id', 'customer', 'order_time', 'order_status', 'total_amount', 'transactions','payment_method']

#     def to_representation(self, instance):
#         response = super().to_representation(instance)
#         response['customer'] = {
#             'customer_id': instance.customer.user.id,
#             'first_name': instance.customer.user.first_name,
#             'last_name': instance.customer.user.last_name,
#             'email': instance.customer.user.email,
#             'phone': instance.customer.phone,
#         }
#         return response


class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['id','order','product']
        # depth = 1



# class OrderItemSerializer(serializers.ModelSerializer):
#     # order = OrderSerializer()
#     # product = ProductDetailSerializer()
#     # order_count = serializers.IntegerField(read_only=True)
#     class Meta:
#         model = OrderItems
#         fields = '__all__'
#         # fields = ['order', 'product', 'quantity', 'price', 'order_count']
#         # depth = 1

#     def to_representation(self, instance):
#         response = super().to_representation(instance)
#         response['order'] = OrderSerializer(instance.order, context=self.context).data
#         response['product'] = ProductDetailSerializer(instance.product, context=self.context).data

#         return response
    


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ['id','customer','address','city','post','default_address']
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['customer'] = CustomerSerializer(instance.customer, context=self.context).data
        return response



class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = ['id', 'customer', 'product', 'rating', 'reviews', 'add_time']

    def __init__(self, *args, **kwargs):
        super(ProductReviewSerializer, self).__init__(*args, **kwargs)
        if self.context.get('view').action in ['list', 'retrieve']:
            self.Meta.depth = 1
        else:
            self.Meta.depth = 0

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['customer'] = CustomerSerializer(instance.customer, context=self.context).data
        return response

        



################### Category ###################

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id','title','detail','total_downloads','category_image']
        depth = 1



class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        depth = 1


class WishListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishList
        fields = '__all__'
        # depth = 1
    
    def __init__(self,*args, **kwargs):
        super(WishListSerializer,self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['customer'] = CustomerSerializer(instance.customer, context=self.context).data
        response['product'] = ProductDetailSerializer(instance.product, context=self.context).data
        return response
    


    class TransactionSerializer(serializers.ModelSerializer):
        class Meta:
            model = Transaction,
            fields = '__all__',


#Vendor report serializer
# class VendorDailyReportSerializer(serializers.Serializer):
#     order_date = serializers.DateField(source='order__order_time__date')
#     total_orders = serializers.IntegerField()



# class VendorDailyReportSerializer(serializers.Serializer):
#     date = serializers.DateField(required=False)
#     month = serializers.DateField(required=False)
#     year = serializers.DateField(required=False)
#     total_orders = serializers.IntegerField()


#date,month and year wise
class VendorDailyReportSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, allow_null=True)
    month = serializers.DateField(required=False, allow_null=True)
    year = serializers.DateField(required=False, allow_null=True)
    total_orders = serializers.IntegerField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # Clean up empty fields
        if not ret.get('date'):
            ret.pop('date', None)
        if not ret.get('month'):
            ret.pop('month', None)
        if not ret.get('year'):
            ret.pop('year', None)

        return ret
    



#search serialzer
# class ProductSerializer(serializers.ModelSerializer):
#     category = serializers.CharField(source='category.title')
#     vendor = serializers.CharField(source='vendor.user.username')

#     class Meta:
#         model = Product
#         fields = ['id', 'title', 'category', 'vendor', 'price', 'image']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.title')
    vendor = serializers.CharField(source='vendor.user.username')
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'category', 'vendor', 'price', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    


class SuperuserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        # Authenticate the user
        user = authenticate(username=username, password=password)

        if user and user.is_superuser:
            return user
        else:
            raise serializers.ValidationError("Invalid credentials or not a superuser.")
        


class ProductSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    customers = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id','category','vendor','title','slug','tags','detail','price','usd_price','demo_url','product_ratings','image','product_file','downloads','publish_status','product_image','hot_deal','order_count','customers']

    def get_order_count(self, obj):
        # Get the count of OrderItems for this product
        return OrderItems.objects.filter(product=obj).aggregate(count=Count('id'))['count']

    def get_customers(self, obj):
        # Get customers who have ordered this product
        order_items = OrderItems.objects.filter(product=obj).select_related('order__customer')
        customers = set(order_item.order.customer for order_item in order_items)
        return CustomerSerializer(customers, many=True).data