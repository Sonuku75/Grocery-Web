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

export interface CartVariantSummary {
  id: string;
  productId?: string;
  product_id?: string;
  sku?: string;
  name?: string;
  unit?: string;
  price: number;
  mrp?: number | null;
  stockQuantity?: number;
  stock_quantity?: number;
  isActive?: boolean;
  is_active?: boolean;
}

export interface CartProductSummary {
  id: string;
  title: string;
  name: string;
  slug: string;
  thumbnailUrl?: string | null;
  thumbnail_url?: string | null;
  imageUrl?: string | null;
  image_url?: string | null;
  images?: string[];
  price?: number;
  unit?: string;
  brand?: string;
  isActive?: boolean;
  is_active?: boolean;
}

export interface CartItem {
  id: string;
  cartId?: string;
  cart_id?: string;
  productId: string;
  product_id?: string;
  variantId?: string;
  variant_id?: string;
  quantity: number;
  unitPrice?: number;
  unit_price?: number;
  lineTotal?: number;
  line_total?: number;
  product: Product;
  variant?: CartVariantSummary;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface Cart {
  id?: string;
  userId?: string;
  user_id?: string;
  items: CartItem[];
  itemCount: number;
  item_count?: number;
  subtotal: number;
  discount: number;
  deliveryFee: number;
  delivery_fee?: number;
  tax: number;
  total: number;
  appliedCoupon?: Coupon | null;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface AddToCartPayload {
  variantId: string;
  variant_id?: string;
  productId?: string;
  product_id?: string;
  quantity?: number;
}

export interface UpdateCartItemPayload {
  quantity: number;
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
  | 'PENDING'
  | 'CONFIRMED'
  | 'PROCESSING'
  | 'SHIPPED'
  | 'OUT_FOR_DELIVERY'
  | 'DELIVERED'
  | 'CANCELLED'
  | 'FAILED'
  // Legacy lowercase compatibility
  | 'order_placed'
  | 'confirmed'
  | 'preparing'
  | 'shipped'
  | 'out_for_delivery'
  | 'delivered'
  | 'cancelled';

export type PaymentStatus =
  | 'PENDING'
  | 'PAID'
  | 'FAILED'
  | 'REFUNDED'
  // Legacy lowercase compatibility
  | 'pending'
  | 'paid'
  | 'failed'
  | 'refunded';

export type FulfillmentStatus =
  | 'UNFULFILLED'
  | 'PROCESSING'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELLED';

export type PaymentMethod = 'card' | 'upi' | 'netbanking' | 'cod';

export interface TrackingStep {
  status: OrderStatus;
  title: string;
  description: string;
  timestamp: string;
  completed: boolean;
  current: boolean;
}

export interface OrderAddressSnapshot {
  fullName: string;
  phone: string;
  addressLine1: string;
  addressLine2?: string | null;
  landmark?: string | null;
  city: string;
  state: string;
  postalCode: string;
  country?: string;
  addressType?: string;
}

export interface OrderStatusHistoryItem {
  id: string;
  orderId?: string;
  fromStatus?: OrderStatus | null;
  toStatus: OrderStatus;
  reason?: string | null;
  changedByUserId?: string | null;
  createdAt: string;
}

export interface OrderItem {
  id: string;
  productId: string;
  variantId?: string;
  productName: string;
  variantName?: string;
  sku?: string;
  unitValue?: number;
  unitType?: string;
  unit?: string;
  unitPrice: number;
  mrp?: number;
  quantity: number;
  lineTotal?: number;
  totalPrice?: number;
  thumbnailUrl?: string;
  productImage?: string;
}

export interface Order {
  id: string;
  orderNumber: string;
  userId: string;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  fulfillmentStatus?: FulfillmentStatus;
  subtotalAmount?: number;
  subtotal?: number;
  discountAmount?: number;
  discount?: number;
  deliveryFee: number;
  taxAmount?: number;
  tax?: number;
  totalAmount?: number;
  total?: number;
  deliverySlot?: string;
  couponCode?: string | null;
  notes?: string | null;
  addressSnapshot?: OrderAddressSnapshot;
  address?: Address;
  items: OrderItem[];
  statusHistory?: OrderStatusHistoryItem[];
  paymentMethod?: PaymentMethod;
  paymentTransactionId?: string;
  trackingHistory?: TrackingStep[];
  estimatedDeliveryTime?: string;
  checkoutSessionId?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface CreateOrderRequest {
  checkoutSessionId: string;
  notes?: string;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
  limit: number;
  offset: number;
}

export type CouponDiscountType = 'PERCENTAGE' | 'FIXED_AMOUNT' | 'percent' | 'fixed';

export interface Coupon {
  id: string;
  code: string;
  name?: string;
  description?: string;
  discountType: CouponDiscountType;
  discount_type?: CouponDiscountType;
  discountValue: number;
  discount_value?: number;
  minimumOrderValue?: number;
  minimum_order_value?: number;
  minOrderAmount: number;
  min_order_amount?: number;
  maximumDiscount?: number | null;
  maximum_discount?: number | null;
  maxDiscount?: number | null;
  max_discount?: number | null;
  startsAt?: string;
  starts_at?: string;
  expiresAt?: string;
  expires_at?: string;
  validUntil: string;
  valid_until?: string;
  usageLimit?: number | null;
  usage_limit?: number | null;
  perUserUsageLimit?: number | null;
  per_user_usage_limit?: number | null;
  usedCount?: number;
  used_count?: number;
  isActive?: boolean;
  is_active?: boolean;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface CouponValidateResponse {
  valid: boolean;
  code: string;
  discount: number;
  message: string;
  coupon?: Coupon | null;
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

// ==========================================
// Module 5: Search & Product Discovery Types
// ==========================================

export type SearchSortOption =
  | 'relevance'
  | 'price_low_to_high'
  | 'price_high_to_low'
  | 'newest'
  | 'featured';

export interface SearchParams {
  q?: string;
  category_id?: string;
  categoryId?: string;
  brand?: string;
  min_price?: number;
  minPrice?: number;
  max_price?: number;
  maxPrice?: number;
  sort?: SearchSortOption;
  cursor?: string;
  limit?: number;
}

export interface SearchItemCategory {
  id: string;
  name: string;
  slug: string;
}

export interface SearchProduct {
  id: string;
  name: string;
  slug: string;
  brand: string;
  imageUrl?: string;
  image_url?: string;
  price: number;
  mrp: number;
  discountPercentage: number;
  discount_percentage?: number;
  unit?: string;
  isFeatured?: boolean;
  is_featured?: boolean;
  category?: SearchItemCategory;
}

export interface SearchResponse {
  query?: string;
  items: SearchProduct[];
  nextCursor?: string;
  next_cursor?: string;
  hasMore: boolean;
  has_more?: boolean;
  total: number;
}

export interface SearchSuggestion {
  type: 'product' | 'brand' | 'category';
  label: string;
  slug?: string;
  id?: string;
  price?: number;
  imageUrl?: string;
  image_url?: string;
}

export interface SearchSuggestionResponse {
  items: SearchSuggestion[];
}

export interface WishlistProduct {
  id: string;
  name: string;
  slug: string;
  brand: string;
  description?: string;
  shortDescription?: string;
  short_description?: string;
  imageUrl?: string;
  image_url?: string;
  isActive?: boolean;
  is_active?: boolean;
  isFeatured?: boolean;
  is_featured?: boolean;
  minPrice?: number;
  min_price?: number;
  minMrp?: number;
  min_mrp?: number;
  maxDiscountPercentage?: number;
  max_discount_percentage?: number;
  primaryVariant?: ProductVariant;
  primary_variant?: ProductVariant;
  variants?: ProductVariant[];
  images?: ProductImage[];
  category?: Category;
  categoryId?: string;
  category_id?: string;
  rating?: number;
  ratingCount?: number;
  rating_count?: number;
}

export interface WishlistItem {
  id: string;
  productId: string;
  product_id?: string;
  product: Product;
  createdAt: string;
  created_at?: string;
}

export interface WishlistResponse {
  items: WishlistItem[];
  count: number;
  nextCursor?: string;
  next_cursor?: string;
  hasMore: boolean;
  has_more?: boolean;
}

export interface WishlistCheckResponse {
  productId: string;
  product_id?: string;
  isWishlisted: boolean;
  is_wishlisted?: boolean;
}

export interface WishlistRemoveResponse {
  productId: string;
  product_id?: string;
  removed: boolean;
  message: string;
}

// =============================================================================
// Module 9: Checkout Types
// =============================================================================

export type CheckoutStatus = 'ACTIVE' | 'COMPLETED' | 'CANCELLED' | 'EXPIRED';

export interface CheckoutItemSnapshot {
  variantId: string;
  variant_id?: string;
  productId: string;
  product_id?: string;
  sku?: string;
  productTitle: string;
  product_title?: string;
  variantName?: string;
  variant_name?: string;
  unit?: string;
  quantity: number;
  unitPrice: number;
  unit_price?: number;
  lineTotal: number;
  line_total?: number;
  thumbnailUrl?: string;
  thumbnail_url?: string;
}

export interface CheckoutAddressSnapshot {
  id?: string;
  recipientName: string;
  recipient_name?: string;
  phone: string;
  mobile?: string;
  addressLine1: string;
  address_line_1?: string;
  addressLine2?: string;
  address_line_2?: string;
  landmark?: string;
  city: string;
  state: string;
  country?: string;
  postalCode: string;
  postal_code?: string;
  label?: string;
  latitude?: number;
  longitude?: number;
}

export interface CheckoutPreviewRequest {
  addressId?: string;
  address_id?: string;
  deliveryMethod?: string;
  delivery_method?: string;
  deliverySlot?: string;
  delivery_slot?: string;
}

export interface CheckoutConfirmRequest {
  checkoutSessionId: string;
  checkout_session_id?: string;
  deliverySlot?: string;
  delivery_slot?: string;
  notes?: string;
}

export interface CheckoutSummary {
  id: string;
  userId: string;
  user_id?: string;
  cartId: string;
  cart_id?: string;
  status: CheckoutStatus;
  items: CheckoutItemSnapshot[];
  address?: CheckoutAddressSnapshot | null;
  subtotal: number;
  discount: number;
  deliveryFee: number;
  delivery_fee?: number;
  tax: number;
  total: number;
  currency: string;
  coupon?: Coupon | null;
  deliveryMethod: string;
  delivery_method?: string;
  deliverySlot?: string;
  delivery_slot?: string;
  expiresAt: string;
  expires_at?: string;
  priceChanged?: boolean;
  price_changed?: boolean;
  warningMessage?: string | null;
  warning_message?: string | null;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface CheckoutConfirmResponse {
  checkoutStatus: string;
  checkout_status?: string;
  checkoutSessionId: string;
  checkout_session_id?: string;
  summary: CheckoutSummary;
  message: string;
}
