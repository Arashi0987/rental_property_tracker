'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Loader2, Building, DollarSign, TrendingUp, Calculator } from 'lucide-react'

interface Property {
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  sqft: number
  property_type: string
  estimated_rent: number
  monthly_payment: number
  monthly_taxes: number
  monthly_insurance: number
  total_monthly_cost: number
  monthly_cash_flow: number
  annual_return: number
  investment_rating: string
}

interface SearchParams {
  location: string
  mortgage_rate: number
  desired_return: number
  maintenance_rate: number
  management_fee: number
  vacancy_rate: number
}

export default function RealEstateAnalyzer() {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    location: '',
    mortgage_rate: 7.0,
    desired_return: 10.0,
    maintenance_rate: 1.5,
    management_fee: 8.0,
    vacancy_rate: 6.0
  })
  
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(false)
  const [currentMortgageRate, setCurrentMortgageRate] = useState<number | null>(null)

  useEffect(() => {
    // Fetch current mortgage rate on component mount
    fetchMortgageRate()
  }, [])

  const fetchMortgageRate = async () => {
    try {
      const response = await fetch('http://localhost:8000/mortgage-rate')
      if (response.ok) {
        const data = await response.json()
        setCurrentMortgageRate(data.rate * 100) // Convert to percentage
        setSearchParams(prev => ({ ...prev, mortgage_rate: data.rate * 100 }))
      }
    } catch (error) {
      console.error('Error fetching mortgage rate:', error)
    }
  }

  const handleSearch = async () => {
    if (!searchParams.location.trim()) {
      alert('Please enter a location')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/analyze-properties', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: searchParams.location,
          mortgage_rate: searchParams.mortgage_rate / 100, // Convert to decimal
          desired_return: searchParams.desired_return,
          maintenance_rate: searchParams.maintenance_rate / 100,
          management_fee: searchParams.management_fee / 100,
          vacancy_rate: searchParams.vacancy_rate / 100
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setProperties(data.properties)
      } else {
        alert('Error analyzing properties. Please try again.')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Error connecting to server. Please make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'Profitable': return 'bg-green-100 text-green-800 border-green-200'
      case 'Cash Flowing': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'Break Even': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'Not Profitable': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Building className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-slate-900">Real Estate Investment Analyzer</h1>
          </div>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Find profitable rental properties by analyzing cash flow, returns, and investment potential
          </p>
        </div>

        {/* Search Form */}
        <Card className="mb-8 max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Investment Parameters
            </CardTitle>
            <CardDescription>
              Enter your investment criteria to analyze properties
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Location */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="location">Location (City, State or ZIP)</Label>
                <Input
                  id="location"
                  placeholder="e.g., Austin, TX or 78701"
                  value={searchParams.location}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, location: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mortgage_rate">
                  Mortgage Rate (%)
                  {currentMortgageRate && (
                    <span className="text-sm text-slate-500 ml-2">
                      Current: {formatPercentage(currentMortgageRate)}
                    </span>
                  )}
                </Label>
                <Input
                  id="mortgage_rate"
                  type="number"
                  step="0.1"
                  value={searchParams.mortgage_rate}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, mortgage_rate: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>

            {/* Investment Parameters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="desired_return">Desired Annual Return (%)</Label>
                <Input
                  id="desired_return"
                  type="number"
                  step="0.1"
                  value={searchParams.desired_return}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, desired_return: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="maintenance_rate">Maintenance Rate (% annually)</Label>
                <Input
                  id="maintenance_rate"
                  type="number"
                  step="0.1"
                  value={searchParams.maintenance_rate}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, maintenance_rate: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="management_fee">Management Fee (% of rent)</Label>
                <Input
                  id="management_fee"
                  type="number"
                  step="0.1"
                  value={searchParams.management_fee}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, management_fee: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="vacancy_rate">Vacancy Rate (%)</Label>
                <Input
                  id="vacancy_rate"
                  type="number"
                  step="0.1"
                  value={searchParams.vacancy_rate}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, vacancy_rate: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>

            <Button 
              onClick={handleSearch} 
              disabled={loading || !searchParams.location.trim()}
              className="w-full md:w-auto"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing Properties...
                </>
              ) : (
                <>
                  <TrendingUp className="mr-2 h-4 w-4" />
                  Analyze Properties
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {properties.length > 0 && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Investment Analysis Results</h2>
              <p className="text-slate-600">Found {properties.length} properties • Sorted by investment potential</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {properties.map((property, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{property.address}</CardTitle>
                        <CardDescription className="text-xl font-semibold text-slate-900 mt-1">
                          {formatCurrency(property.price)}
                        </CardDescription>
                      </div>
                      <Badge className={getRatingColor(property.investment_rating)}>
                        {property.investment_rating}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Property Details */}
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center">
                        <div className="font-semibold">{property.bedrooms}</div>
                        <div className="text-slate-500">Bedrooms</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold">{property.bathrooms}</div>
                        <div className="text-slate-500">Bathrooms</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold">{property.sqft.toLocaleString()}</div>
                        <div className="text-slate-500">Sq Ft</div>
                      </div>
                    </div>

                    <Separator />

                    {/* Financial Analysis */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">Estimated Rent</span>
                        <span className="font-semibold">{formatCurrency(property.estimated_rent)}/mo</span>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Mortgage Payment</span>
                          <span>{formatCurrency(property.monthly_payment)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Taxes</span>
                          <span>{formatCurrency(property.monthly_taxes)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Insurance</span>
                          <span>{formatCurrency(property.monthly_insurance)}</span>
                        </div>
                      </div>

                      <Separator />

                      <div className="flex justify-between items-center font-semibold">
                        <span>Monthly Cash Flow</span>
                        <span className={property.monthly_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {property.monthly_cash_flow >= 0 ? '+' : ''}{formatCurrency(property.monthly_cash_flow)}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-slate-600">Annual Return</span>
                        <span className={`font-semibold ${property.annual_return >= searchParams.desired_return ? 'text-green-600' : 'text-slate-900'}`}>
                          {formatPercentage(property.annual_return)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && properties.length === 0 && (
          <div className="text-center py-12">
            <DollarSign className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Ready to Analyze Properties</h3>
            <p className="text-slate-600">Enter a location and your investment criteria to get started</p>
          </div>
        )}
      </div>
    </div>
  )
}
