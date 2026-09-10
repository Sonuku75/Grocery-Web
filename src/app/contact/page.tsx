"use client";

import React, { useState } from "react";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { Mail, Phone, MapPin, Clock, MessageSquare, CheckCircle2 } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function ContactPage() {
  const { showToast } = useToast();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
      showToast("Message sent! Our customer support team will reply within 1 hour.", "success");
    }, 600);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      <Breadcrumb items={[{ label: "Contact Us" }]} />

      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">
          How Can We Help You?
        </h1>
        <p className="text-xs sm:text-sm text-slate-500">
          Have questions about your order, delivery hub coverage, or vendor partnership? Reach out anytime.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Contact Info Cards */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
              <Phone className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Phone Support</h3>
              <p className="text-xs text-slate-500 mt-0.5">Mon - Sun, 6:00 AM - 11:00 PM</p>
              <a href="tel:+18005550199" className="text-xs font-bold text-brand-600 mt-2 block hover:underline">
                +1 (800) 555-0199 (Toll Free)
              </a>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Email Customer Care</h3>
              <p className="text-xs text-slate-500 mt-0.5">Average response time: 20 minutes</p>
              <a href="mailto:support@cartify.com" className="text-xs font-bold text-brand-600 mt-2 block hover:underline">
                support@cartify.com
              </a>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-card flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
              <MapPin className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">San Francisco Headquarters</h3>
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                Cartify Inc., 500 Howard Street, Suite 400, San Francisco, CA 94105
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-card">
          {submitted ? (
            <div className="text-center py-12 space-y-3">
              <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Message Received!</h3>
              <p className="text-xs text-slate-500 max-w-xs mx-auto">
                Thank you for getting in touch. One of our support representatives will follow up shortly.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSubmitted(false);
                  setName("");
                  setEmail("");
                  setSubject("");
                  setMessage("");
                }}
              >
                Send Another Message
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100">
                Send Us a Message
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Your Name"
                  placeholder="e.g. Alex Rivera"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
                <Input
                  label="Email Address"
                  type="email"
                  placeholder="alex@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <Input
                label="Subject"
                placeholder="e.g. Question about order CT-89241"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
              />

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                  Your Message
                </label>
                <textarea
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Please describe how we can assist you..."
                  className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-200 bg-white placeholder:text-slate-400 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                  required
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={loading}
              >
                Submit Message
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
