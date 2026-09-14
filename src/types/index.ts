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
  productId?: string;
  product_id?: string;
  userId?: string;
  user_id?: string;
  userName?: string;
  reviewerName?: string;
  reviewer_name?: string;
  userAvatar?: string;
  rating: number;
  title?: string;
  body?: string;
  comment?: string;
  status?: string;
  isVerifiedPurchase?: boolean;
  is_verified_purchase?: boolean;
  helpfulCount?: number;
  helpful_count?: number;
  userVotedHelpful?: boolean;
  user_voted_helpful?: boolean;
  isOwnReview?: boolean;
  is_own_review?: boolean;
  createdAt: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface RatingSummary {
  averageRating: number;
  average_rating?: number;
  totalReviews: number;
  total_reviews?: number;
  distribution: {
    "1": number;
    "2": number;
    "3": number;
    "4": number;
    "5": number;
    [key: string]: number;
  };
}

export interface ReviewableItem {
  orderItemId: string;
  order_item_id?: string;
  orderId: string;
  order_id?: string;
  orderNumber: string;
  order_number?: string;
  productId: string;
  product_id?: string;
  productName: string;
  product_name?: string;
  variantName?: string;
  variant_name?: string;
  deliveredAt?: string;
  delivered_at?: string;
}

export interface ReviewEligibility {
  canReview: boolean;
  can_review?: boolean;
  reason?: string | null;
  reviewableItems: ReviewableItem[];
  reviewable_items?: ReviewableItem[];
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
  availableQuantity?: number;
  available_quantity?: number;
  isAvailable?: boolean;
  is_available?: boolean;
  isLowStock?: boolean;
  is_low_stock?: boolean;
  isOutOfStock?: boolean;
  is_out_of_stock?: boolean;
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
  | 'AUTHORIZED'
  | 'PAID'
  | 'FAILED'
  | 'CANCELLED'
  | 'REFUND_PENDING'
  | 'PARTIALLY_REFUNDED'
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

export type PaymentMethod =
  | 'UPI'
  | 'CARD'
  | 'NET_BANKING'
  | 'WALLET'
  | 'COD'
  // Legacy lowercase compatibility
  | 'card'
  | 'upi'
  | 'netbanking'
  | 'cod';

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

// =============================================================================
// Module 11: Inventory Types
// =============================================================================

export type InventoryTransactionType =
  | 'INITIAL'
  | 'RESTOCK'
  | 'SALE'
  | 'CANCELLATION'
  | 'RETURN'
  | 'DAMAGE'
  | 'ADJUSTMENT';

export interface CustomerInventoryResponse {
  variantId: string;
  variant_id?: string;
  availableQuantity: number;
  available_quantity?: number;
  isAvailable: boolean;
  is_available?: boolean;
  isLowStock: boolean;
  is_low_stock?: boolean;
}

export interface AdminInventoryResponse {
  id: string;
  variantId: string;
  variant_id?: string;
  productId?: string;
  product_id?: string;
  productTitle?: string;
  product_title?: string;
  variantName?: string;
  variant_name?: string;
  sku?: string;
  quantity: number;
  reservedQuantity: number;
  reserved_quantity?: number;
  availableQuantity: number;
  available_quantity?: number;
  lowStockThreshold: number;
  low_stock_threshold?: number;
  isActive: boolean;
  is_active?: boolean;
  isLowStock: boolean;
  is_low_stock?: boolean;
  isOutOfStock: boolean;
  is_out_of_stock?: boolean;
  createdAt: string;
  created_at?: string;
  updatedAt: string;
  updated_at?: string;
}

export interface AdminInventoryListResponse {
  items: AdminInventoryResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface InventoryTransactionResponse {
  id: string;
  inventoryId: string;
  inventory_id?: string;
  variantId: string;
  variant_id?: string;
  transactionType: InventoryTransactionType;
  transaction_type?: InventoryTransactionType;
  quantityChange: number;
  quantity_change?: number;
  quantityBefore: number;
  quantity_before?: number;
  quantityAfter: number;
  quantity_after?: number;
  referenceType?: string | null;
  reference_type?: string | null;
  referenceId?: string | null;
  reference_id?: string | null;
  reason?: string;
  createdByUserId?: string | null;
  created_by_user_id?: string | null;
  createdAt: string;
  created_at?: string;
}

export interface AdminAdjustStockPayload {
  quantityChange: number;
  quantity_change?: number;
  transactionType?: InventoryTransactionType;
  transaction_type?: InventoryTransactionType;
  reason: string;
  referenceType?: string;
  reference_type?: string;
  referenceId?: string;
  reference_id?: string;
}

// Module 12: Payments & High-Security Payment Infrastructure
export interface Payment {
  id: string;
  orderId: string;
  order_id?: string;
  userId: string;
  user_id?: string;
  provider: string;
  providerPaymentId?: string | null;
  provider_payment_id?: string | null;
  providerOrderId?: string | null;
  provider_order_id?: string | null;
  paymentMethod: PaymentMethod;
  payment_method?: PaymentMethod;
  amount: number | string;
  currency: string;
  status: PaymentStatus;
  failureCode?: string | null;
  failure_code?: string | null;
  failureMessage?: string | null;
  failure_message?: string | null;
  paidAt?: string | null;
  paid_at?: string | null;
  createdAt: string;
  created_at?: string;
}

export interface InitiatePaymentRequest {
  orderId: string;
  order_id?: string;
  paymentMethod: PaymentMethod;
  payment_method?: PaymentMethod;
  provider?: string;
}

export interface InitiatePaymentResponse {
  paymentId: string;
  payment_id?: string;
  orderId: string;
  order_id?: string;
  amount: number | string;
  currency: string;
  provider: string;
  providerOrderId?: string | null;
  provider_order_id?: string | null;
  paymentMethod: PaymentMethod;
  payment_method?: PaymentMethod;
  status: PaymentStatus;
  clientSecret?: string | null;
  client_secret?: string | null;
  gatewayData?: Record<string, any>;
  gateway_data?: Record<string, any>;
}

export interface VerifyPaymentRequest {
  paymentId: string;
  payment_id?: string;
  providerPaymentId?: string;
  provider_payment_id?: string;
  providerOrderId?: string;
  provider_order_id?: string;
  providerSignature?: string;
  provider_signature?: string;
}

export interface PaymentRefund {
  id: string;
  paymentId: string;
  payment_id?: string;
  amount: number | string;
  currency: string;
  reason?: string;
  status: 'PENDING' | 'PROCESSED' | 'FAILED';
  createdAt: string;
  created_at?: string;
}

// ==========================================
// Module 13: Notifications & Device Types
// ==========================================

export type NotificationChannel = 'IN_APP' | 'EMAIL' | 'SMS' | 'PUSH';

export type NotificationPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type NotificationStatus = 'UNREAD' | 'READ' | 'EXPIRED';

export type NotificationCategory =
  | 'ORDER_UPDATES'
  | 'PAYMENT_UPDATES'
  | 'PROMOTIONS'
  | 'SECURITY_ALERTS';

export interface NotificationItem {
  id: string;
  userId: string;
  user_id?: string;
  type: string;
  title: string;
  body: string;
  data?: Record<string, any>;
  priority: NotificationPriority | string;
  status: NotificationStatus | string;
  referenceKey?: string | null;
  reference_key?: string | null;
  createdAt: string;
  created_at?: string;
  readAt?: string | null;
  read_at?: string | null;
  expiresAt?: string | null;
  expires_at?: string | null;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unreadCount: number;
  unread_count?: number;
  nextCursor?: string | null;
  next_cursor?: string | null;
}

export interface UnreadCountResponse {
  unreadCount: number;
  unread_count?: number;
}

export interface NotificationPreferenceItem {
  category: NotificationCategory | string;
  channel: NotificationChannel | string;
  isEnabled: boolean;
  is_enabled?: boolean;
  isMandatory: boolean;
  is_mandatory?: boolean;
}

export interface NotificationPreferencesResponse {
  preferences: NotificationPreferenceItem[];
}

export interface UpdateNotificationPreferenceRequest {
  category: string;
  channel: string;
  isEnabled: boolean;
}

export interface DeviceItem {
  id: string;
  platform: 'WEB' | 'ANDROID' | 'IOS' | string;
  maskedToken: string;
  masked_token?: string;
  appVersion?: string | null;
  app_version?: string | null;
  isActive: boolean;
  is_active?: boolean;
  lastSeenAt: string;
  last_seen_at?: string;
  createdAt: string;
  created_at?: string;
}

export interface DeviceListResponse {
  items: DeviceItem[];
}

export interface RegisterDeviceRequest {
  platform: 'WEB' | 'ANDROID' | 'IOS' | string;
  deviceToken: string;
  appVersion?: string;
}

