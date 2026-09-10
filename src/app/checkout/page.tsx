"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Address, PaymentMethod } from "@/types";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { addressService } from "@/services/addressService";
import { orderService } from "@/services/orderService";
import { AddressModal } from "@/components/addresses/AddressModal";
import { Button } from "@/components/common/Button";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { formatCurrency } from "@/lib/utils";
import {
  MapPin,
  Clock,
  CreditCard,
  CheckCircle2,
  Plus,
  ArrowRight,
  ShieldCheck,
  Building,
  Home,
  QrCode,
  Banknote,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, clearCart } = useCart();
  const { user } = useAuth();
  const { showToast } = useToast();

  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>("");
  const [isAddressModalOpen, setIsAddressModalOpen] = useState(false);

  const [deliverySlot, setDeliverySlot] = useState("Today • Express 15-Minute Delivery");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("card");

  // Payment mock card details
  const [cardNumber, setCardNumber] = useState("4242 •••• •••• 4242");
  const [cardExpiry, setCardExpiry] = useState("12/28");
  const [cardCvv, setCardCvv] = useState("888");

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadAddresses() {
      const addrs = await addressService.getAddresses();
      setAddresses(addrs);
      const defaultAddr = addrs.find((a) => a.isDefault) || addrs[0];
      if (defaultAddr) {
        setSelectedAddressId(defaultAddr.id);
      }
    }
    loadAddresses();
  }, []);

  const selectedAddress = addresses.find((a) => a.id === selectedAddressId) || addresses[0];

  const handleCreateAddress = async (data: Parameters<typeof addressService.addAddress>[0]) => {
    const created = await addressService.addAddress(data);
    setAddresses((prev) => [created, ...prev]);
    setSelectedAddressId(created.id);
    showToast("Delivery address added!", "success");
  };

  const handlePlaceOrder = async () => {
    if (!selectedAddress) {
      showToast("Please select or add a delivery address", "error");
      setCurrentStep(1);
      return;
    }

    setLoading(true);
    try {
      const orderItems = cart.items.map((item) => ({
        id: "oi-" + Math.random().toString(36).substring(2, 8),
        productId: item.productId,
        productName: item.product.name,
        productImage: item.product.images[0],
        unitPrice: item.product.price,
        quantity: item.quantity,
        totalPrice: item.product.price * item.quantity,
        unit: item.product.unit,
      }));

      const newOrder = await orderService.createOrder({
        userId: user?.id || "usr-demo",
        address: selectedAddress,
        items: orderItems,
        subtotal: cart.subtotal,
        discount: cart.discount,
        deliveryFee: cart.deliveryFee,
        tax: cart.tax,
        total: cart.total,
        paymentMethod,
        paymentStatus: paymentMethod === "cod" ? "pending" : "paid",
        deliverySlot,
      });

      await clearCart();
      showToast("Order placed successfully!", "success");
      router.push(`/order-confirmation/${newOrder.id}`);
    } catch (err) {
      showToast("Failed to place order. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  };

  if (cart.items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <h2 className="text-xl font-bold text-slate-800 mb-2">Your Cart is Empty</h2>
        <p className="text-xs text-slate-500 mb-4">
          Add fresh produce and essentials to proceed through checkout.
        </p>
        <Link href="/products">
          <Button variant="primary">Shop Products</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <Breadcrumb
        items={[
          { label: "Cart", href: "/cart" },
          { label: "Checkout" },
        ]}
      />

      {/* Stepper Progress Header */}
      <div className="max-w-3xl mx-auto">
        <div className="grid grid-cols-4 gap-2 text-center text-xs font-bold">
          {[
            { step: 1, title: "1. Address" },
            { step: 2, title: "2. Slot" },
            { step: 3, title: "3. Payment" },
            { step: 4, title: "4. Review" },
          ].map((s) => (
            <button
              key={s.step}
              onClick={() => setCurrentStep(s.step as 1 | 2 | 3 | 4)}
              className={`p-3 rounded-2xl border transition-all ${
                currentStep === s.step
                  ? "border-brand-600 bg-brand-50 text-brand-700 shadow-xs"
                  : currentStep > s.step
                  ? "border-slate-200 bg-slate-50 text-slate-700"
                  : "border-slate-100 text-slate-400 opacity-60"
              }`}
            >
              {s.title}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Interactive Step Box */}
        <div className="lg:col-span-8 bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-card space-y-6">
          {/* STEP 1: ADDRESS */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Select Delivery Address</h2>
                  <p className="text-xs text-slate-500">Choose where we should deliver your order</p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  leftIcon={<Plus className="w-3.5 h-3.5" />}
                  onClick={() => setIsAddressModalOpen(true)}
                >
                  Add Address
                </Button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {addresses.map((addr) => (
                  <div
                    key={addr.id}
                    onClick={() => setSelectedAddressId(addr.id)}
                    className={`p-4 rounded-2xl border-2 cursor-pointer transition-all ${
                      selectedAddressId === addr.id
                        ? "border-brand-600 bg-brand-50/40 shadow-xs"
                        : "border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="flex items-center gap-1.5 text-xs font-bold capitalize text-slate-800">
                        {addr.addressType === "home" ? (
                          <Home className="w-3.5 h-3.5 text-brand-600" />
                        ) : (
                          <Building className="w-3.5 h-3.5 text-brand-600" />
                        )}
                        {addr.addressType}
                      </span>
                      {selectedAddressId === addr.id && (
                        <CheckCircle2 className="w-4 h-4 text-brand-600" />
                      )}
                    </div>
                    <p className="text-xs font-bold text-slate-900">{addr.fullName}</p>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {addr.houseFlat}, {addr.street}, {addr.area}, {addr.city} {addr.pincode}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-2 font-medium">{addr.mobile}</p>
                  </div>
                ))}
              </div>

              <div className="pt-4 flex justify-end">
                <Button
                  variant="primary"
                  onClick={() => setCurrentStep(2)}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Continue to Delivery Slot
                </Button>
              </div>
            </div>
          )}

          {/* STEP 2: DELIVERY SLOT */}
          {currentStep === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div className="pb-3 border-b border-slate-100">
                <h2 className="text-lg font-bold text-slate-900">Choose Delivery Speed</h2>
                <p className="text-xs text-slate-500">Select when you want your groceries delivered</p>
              </div>

              <div className="space-y-3">
                {[
                  {
                    id: "express",
                    title: "Today • Express 15-Minute Delivery",
                    desc: "Handpicked & dispatched immediately via electric courier",
                    tag: "⚡ Recommended",
                  },
                  {
                    id: "today-evening",
                    title: "Today • Evening Slot (5:00 PM - 6:00 PM)",
                    desc: "Delivered fresh after work hours",
                  },
                  {
                    id: "tomorrow-morning",
                    title: "Tomorrow Morning (8:00 AM - 9:00 AM)",
                    desc: "Fresh morning sourdough, eggs & cold milk for breakfast",
                  },
                ].map((slot) => (
                  <div
                    key={slot.id}
                    onClick={() => setDeliverySlot(slot.title)}
                    className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex items-center justify-between ${
                      deliverySlot === slot.title
                        ? "border-brand-600 bg-brand-50/40 shadow-xs"
                        : "border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold text-slate-900">{slot.title}</h4>
                        {slot.tag && (
                          <span className="text-[10px] font-bold text-accent-700 bg-accent-100 px-2 py-0.5 rounded-full">
                            {slot.tag}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500">{slot.desc}</p>
                    </div>
                    {deliverySlot === slot.title && (
                      <CheckCircle2 className="w-5 h-5 text-brand-600 shrink-0" />
                    )}
                  </div>
                ))}
              </div>

              <div className="pt-4 flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep(1)}>
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={() => setCurrentStep(3)}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Continue to Payment
                </Button>
              </div>
            </div>
          )}

          {/* STEP 3: PAYMENT METHOD */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div className="pb-3 border-b border-slate-100">
                <h2 className="text-lg font-bold text-slate-900">Select Payment Method</h2>
                <p className="text-xs text-slate-500">All transactions are encrypted and 100% secure</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { id: "card" as PaymentMethod, name: "Credit / Debit Card", icon: CreditCard },
                  { id: "upi" as PaymentMethod, name: "Instant UPI / QR", icon: QrCode },
                  { id: "cod" as PaymentMethod, name: "Cash on Delivery", icon: Banknote },
                ].map((m) => {
                  const Icon = m.icon;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setPaymentMethod(m.id)}
                      className={`p-4 rounded-2xl border-2 flex flex-col items-center text-center gap-2 transition-all ${
                        paymentMethod === m.id
                          ? "border-brand-600 bg-brand-50/50 text-brand-700 font-bold"
                          : "border-slate-200 text-slate-600 hover:border-slate-300"
                      }`}
                    >
                      <Icon className="w-6 h-6" />
                      <span className="text-xs">{m.name}</span>
                    </button>
                  );
                })}
              </div>

              {paymentMethod === "card" && (
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 mt-4">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                      Card Number
                    </label>
                    <input
                      type="text"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(e.target.value)}
                      className="w-full px-3 py-2 text-xs font-mono rounded-xl border border-slate-200 bg-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                        Expiry Date
                      </label>
                      <input
                        type="text"
                        value={cardExpiry}
                        onChange={(e) => setCardExpiry(e.target.value)}
                        className="w-full px-3 py-2 text-xs font-mono rounded-xl border border-slate-200 bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                        CVV / CVC
                      </label>
                      <input
                        type="password"
                        value={cardCvv}
                        onChange={(e) => setCardCvv(e.target.value)}
                        className="w-full px-3 py-2 text-xs font-mono rounded-xl border border-slate-200 bg-white"
                      />
                    </div>
                  </div>
                </div>
              )}

              {paymentMethod === "upi" && (
                <div className="p-4 rounded-2xl bg-brand-50/40 border border-brand-200 text-center space-y-2 mt-4">
                  <p className="text-xs font-bold text-brand-900">Pay using your preferred UPI app</p>
                  <p className="text-[11px] text-slate-500">
                    Google Pay, PhonePe, Paytm, or BHIM. A secure payment prompt will be issued upon placing order.
                  </p>
                </div>
              )}

              {paymentMethod === "cod" && (
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1 mt-4 text-xs text-slate-600">
                  <p className="font-bold text-slate-800">Cash / UPI on Delivery</p>
                  <p>You can pay via cash or scan rider&apos;s QR code when the order arrives at your door.</p>
                </div>
              )}

              <div className="pt-4 flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep(2)}>
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={() => setCurrentStep(4)}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Review Order
                </Button>
              </div>
            </div>
          )}

          {/* STEP 4: REVIEW & PLACE ORDER */}
          {currentStep === 4 && (
            <div className="space-y-6 animate-fade-in">
              <div className="pb-3 border-b border-slate-100">
                <h2 className="text-lg font-bold text-slate-900">Review & Place Your Order</h2>
                <p className="text-xs text-slate-500">Confirm all details before dispatch</p>
              </div>

              {/* Delivery Details Card */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-slate-800">
                  <span>Delivering to: {selectedAddress?.fullName}</span>
                  <button
                    onClick={() => setCurrentStep(1)}
                    className="text-brand-600 hover:underline"
                  >
                    Change
                  </button>
                </div>
                <p className="text-slate-600">
                  {selectedAddress?.houseFlat}, {selectedAddress?.street}, {selectedAddress?.area},{" "}
                  {selectedAddress?.city} ({selectedAddress?.pincode})
                </p>
                <div className="pt-2 border-t border-slate-200/80 flex items-center justify-between text-slate-500">
                  <span>Delivery Slot: <strong>{deliverySlot}</strong></span>
                  <span>Payment: <strong>{paymentMethod.toUpperCase()}</strong></span>
                </div>
              </div>

              {/* Ordered Items Preview */}
              <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                {cart.items.map((item) => (
                  <div key={item.id} className="py-2.5 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-3">
                      <div className="relative w-10 h-10 rounded-lg overflow-hidden bg-slate-100 shrink-0">
                        <Image
                          src={item.product.images[0]}
                          alt={item.product.name}
                          fill
                          className="object-cover"
                        />
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">{item.product.name}</p>
                        <p className="text-slate-400">Qty: {item.quantity} • {item.product.unit}</p>
                      </div>
                    </div>
                    <span className="font-bold text-slate-900">
                      {formatCurrency(item.product.price * item.quantity)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="pt-4 flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep(3)}>
                  Back
                </Button>
                <Button
                  variant="primary"
                  size="lg"
                  isLoading={loading}
                  onClick={handlePlaceOrder}
                  leftIcon={<CheckCircle2 className="w-5 h-5" />}
                >
                  Place Order ({formatCurrency(cart.total)})
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Right Summary Sidebar */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-card space-y-4">
          <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
            Cart Total ({cart.itemCount} items)
          </h3>

          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex justify-between">
              <span>Subtotal</span>
              <span className="font-bold text-slate-900">{formatCurrency(cart.subtotal)}</span>
            </div>
            {cart.discount > 0 && (
              <div className="flex justify-between text-brand-600 font-bold">
                <span>Discount</span>
                <span>-{formatCurrency(cart.discount)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Delivery Fee</span>
              <span>{cart.deliveryFee === 0 ? <strong className="text-brand-600 font-bold">FREE</strong> : formatCurrency(cart.deliveryFee)}</span>
            </div>
            <div className="flex justify-between">
              <span>Taxes</span>
              <span>{formatCurrency(cart.tax)}</span>
            </div>
            <div className="flex justify-between pt-2 border-t border-slate-200 text-base font-black text-slate-900">
              <span>Grand Total</span>
              <span>{formatCurrency(cart.total)}</span>
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-brand-50/40 border border-brand-100 text-[11px] text-brand-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-600 shrink-0" />
            <span>Encrypted 256-bit SSL transaction</span>
          </div>
        </div>
      </div>

      <AddressModal
        isOpen={isAddressModalOpen}
        onClose={() => setIsAddressModalOpen(false)}
        onSave={handleCreateAddress}
      />
    </div>
  );
}
