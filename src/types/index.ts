export type Role = 'customer' | 'admin';

export interface User {
  id: string;
  name?: string;
  fullName: string;
  email: string;
  phone?: string;
  mobile: string;
  avatarUrl?: string;
  role: Role;
  isActive: boolean;
  isVerified?: boolean;
  createdAt: string;
  updatedAt?: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface LoginPayload {
  identifier?: string; // email or mobile
  email?: string;
  password: string;
}

export interface RegisterPayload {
  name?: string;
  fullName: string;
  email: string;
  phone?: string;
  mobile: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  newPassword: string;
}

export interface ChangePasswordPayload {
  currentPassword: string;
  newPassword: string;
}

export interface UserUpdatePayload {
  name?: string;
  phone?: string;
  avatarUrl?: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description?: string;
  icon?: string;
  imageUrl?: string;
  image_url?: string;
  parentId?: string | null;
  parent_id?: string | null;
  sortOrder?: number;
  sort_order?: number;
  isActive?: boolean;
  is_active?: boolean;
  itemCount?: number;
  subcategories?: Category[];
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface CategoryListResponse {
  items: Category[];
  total: number;
}

export interface CategoryInput {
  name: string;
  slug?: string;
  description?: string;
  icon?: string;
  imageUrl?: string;
  parentId?: string | null;
  sortOrder?: number;
  isActive?: boolean;
}

export interface ProductReview {
  id: string;
  productId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  rating: number;
  comment: string;
  createdAt: string;
}

export interface ProductVariant {
  id: string;
  productId?: string;
  product_id?: string;
  sku: string;
  name: string;
  unitValue: number;
  unit_value?: number;
  unitType: string;
  unit_type?: string;
  price: number;
  mrp: number;
  discountPercentage?: number;
  discount_percentage?: number;
  isActive?: boolean;
  is_active?: boolean;
  sortOrder?: number;
  sort_order?: number;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface ProductImage {
  id: string;
  productId?: string;
  product_id?: string;
  imageUrl: string;
  image_url?: string;
  altText?: string;
  alt_text?: string;
  sortOrder?: number;
  sort_order?: number;
  isPrimary?: boolean;
  is_primary?: boolean;
  createdAt?: string;
  created_at?: string;
}

export interface Product {
  id: string;
  slug: string;
  name: string;
  brand: string;
  categoryId: string;
  category_id?: string;
  categoryName?: string;
  category_name?: string;
  categorySlug?: string;
  category_slug?: string;
  category?: Category;
  description: string;
  shortDescription?: string;
  short_description?: string;
  specifications: Record<string, string>;
  price: number;
  originalPrice: number;
  mrp?: number;
  discountPercent: number;
  discountPercentage?: number;
  unit: string; // e.g. "500 g", "1 kg", "Pack of 2"
  stock: number;
  rating: number;
  ratingCount: number;
  imageUrl?: string;
  image_url?: string;
  images: string[];
  productImages?: ProductImage[];
  variants?: ProductVariant[];
  primaryVariant?: ProductVariant;
  isPopular?: boolean;
  isFeatured?: boolean;
  is_featured?: boolean;
  isDeal?: boolean;
  tags: string[];
  inStock: boolean;
  isActive?: boolean;
  is_active?: boolean;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface ProductListResponse {
  items: Product[];
  nextCursor?: string | null;
  hasMore?: boolean;
  total?: number;
}

export interface CartItem {
  id: string;
  productId: string;
  product: Product;
  quantity: number;
}

export interface Cart {
  items: CartItem[];
  itemCount: number;
  subtotal: number;
  discount: number;
  deliveryFee: number;
  tax: number;
  total: number;
  appliedCoupon?: Coupon | null;
}

export type AddressType = 'home' | 'work' | 'other';

export interface Address {
  id: string;
  userId?: string;
  user_id?: string;
  label?: string;
  addressType?: AddressType;
  recipientName?: string;
  recipient_name?: string;
  fullName: string;
  phone?: string;
  mobile: string;
  addressLine1?: string;
  address_line_1?: string;
  houseFlat: string;
  addressLine2?: string;
  address_line_2?: string;
  street: string;
  area: string;
  landmark?: string;
  city: string;
  state: string;
  country?: string;
  postalCode?: string;
  postal_code?: string;
  pincode: string;
  latitude?: number | null;
  longitude?: number | null;
  isDefault: boolean;
  is_default?: boolean;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export type AddressInput = {
  label?: string;
  addressType?: AddressType;
  recipientName?: string;
  fullName: string;
  phone?: string;
  mobile: string;
  addressLine1?: string;
  houseFlat: string;
  addressLine2?: string;
  street: string;
  area: string;
  landmark?: string;
  city: string;
  state: string;
  country?: string;
  postalCode?: string;
  pincode: string;
  latitude?: number | null;
  longitude?: number | null;
  isDefault?: boolean;
  is_default?: boolean;
};

export interface AddressListResponse {
  items: Address[];
  total: number;
}

export type OrderStatus =
  | 'order_placed'
  | 'confirmed'
  | 'preparing'
  | 'shipped'
  | 'out_for_delivery'
  | 'delivered'
  | 'cancelled';

export type PaymentStatus = 'pending' | 'paid' | 'failed' | 'refunded';

export type PaymentMethod = 'card' | 'upi' | 'netbanking' | 'cod';

export interface TrackingStep {
  status: OrderStatus;
  title: string;
  description: string;
  timestamp: string;
  completed: boolean;
  current: boolean;
}

export interface OrderItem {
  id: string;
  productId: string;
  productName: string;
  productImage: string;
  unitPrice: number;
  quantity: number;
  totalPrice: number;
  unit: string;
}

export interface Order {
  id: string;
  orderNumber: string;
  userId: string;
  address: Address;
  items: OrderItem[];
  subtotal: number;
  discount: number;
  deliveryFee: number;
  tax: number;
  total: number;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  paymentMethod: PaymentMethod;
  paymentTransactionId?: string;
  trackingHistory: TrackingStep[];
  deliverySlot?: string;
  estimatedDeliveryTime?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Coupon {
  id: string;
  code: string;
  discountType: 'percent' | 'fixed';
  discountValue: number;
  minOrderAmount: number;
  maxDiscount?: number;
  validUntil: string;
  description: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ProductFilters {
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  minRating?: number;
  brand?: string;
  inStock?: boolean;
  search?: string;
  sortBy?: 'relevance' | 'price_asc' | 'price_desc' | 'rating' | 'newest' | 'popular';
  page?: number;
  limit?: number;
}
