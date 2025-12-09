import { useState, useRef, useEffect, useCallback } from 'react';
import type { PeriodType } from '../types';
import { PERIOD_OPTIONS, PARTNER_CATEGORIES } from '../types';

interface FilterBarProps {
  periodType: PeriodType;
  onPeriodChange: (period: PeriodType, startDate?: string, endDate?: string) => void;
  customStart?: string;
  customEnd?: string;
  selectedPartners: string[];
  onPartnersChange: (partners: string[]) => void;
  showPartnerFilter?: boolean;
}

interface DropdownProps {
  label: string;
  value: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  icon?: string;
}

function Dropdown({ label, value, isOpen, onToggle, children, icon }: DropdownProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        if (isOpen) onToggle();
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onToggle]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={onToggle}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all duration-200 min-w-[180px] ${
          isOpen 
            ? 'bg-white border-green-500 shadow-lg shadow-green-500/10' 
            : 'bg-white border-gray-200 hover:border-green-300 hover:shadow-md'
        }`}
      >
        {icon && <span className="text-lg">{icon}</span>}
        <div className="flex flex-col items-start flex-1">
          <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">{label}</span>
          <span className="text-sm font-medium text-gray-800 truncate max-w-[140px]">
            {value}
          </span>
        </div>
        <svg 
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isOpen && (
        <div 
          className="absolute top-full left-0 mt-2 w-80 bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden animate-fade-in"
          style={{ zIndex: 9999 }}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export default function FilterBar({
  periodType,
  onPeriodChange,
  customStart,
  customEnd,
  selectedPartners,
  onPartnersChange,
  showPartnerFilter = true,
}: FilterBarProps) {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [localStart, setLocalStart] = useState(customStart || '');
  const [localEnd, setLocalEnd] = useState(customEnd || '');
  // Track if we're in "custom mode" without having applied dates yet
  const [showCustomPicker, setShowCustomPicker] = useState(periodType === 'custom');
  // Ref for scrolling to custom date picker
  const customPickerRef = useRef<HTMLDivElement>(null);

  // Sync local state with props
  useEffect(() => {
    if (customStart) setLocalStart(customStart);
    if (customEnd) setLocalEnd(customEnd);
  }, [customStart, customEnd]);

  // Sync showCustomPicker with periodType
  useEffect(() => {
    if (periodType === 'custom') {
      setShowCustomPicker(true);
    }
  }, [periodType]);

  // Scroll to custom picker when it becomes visible
  const scrollToCustomPicker = useCallback(() => {
    setTimeout(() => {
      if (customPickerRef.current) {
        customPickerRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'nearest' 
        });
      }
    }, 50);
  }, []);

  const toggleDropdown = (name: string) => {
    setOpenDropdown(openDropdown === name ? null : name);
  };

  const handlePeriodSelect = (period: PeriodType) => {
    if (period === 'custom') {
      // Just show the date picker, DON'T change the period yet
      setShowCustomPicker(true);
      // Scroll to the custom picker for better UX
      scrollToCustomPicker();
      // Don't call onPeriodChange here - wait for user to apply dates
    } else {
      setShowCustomPicker(false);
      onPeriodChange(period);
      setOpenDropdown(null);
    }
  };

  const handleCustomApply = () => {
    if (localStart && localEnd) {
      onPeriodChange('custom', localStart, localEnd);
      setOpenDropdown(null);
    }
  };

  const handleCategoryToggle = (categoryId: string) => {
    const category = PARTNER_CATEGORIES.find(c => c.id === categoryId);
    if (!category || categoryId === 'all') return;

    const categoryPartners = category.partners;
    const allSelected = categoryPartners.every(p => selectedPartners.includes(p));

    if (allSelected) {
      // Deselect all from this category
      onPartnersChange(selectedPartners.filter(p => !categoryPartners.includes(p)));
    } else {
      // Select all from this category
      const newPartners = [...new Set([...selectedPartners, ...categoryPartners])];
      onPartnersChange(newPartners);
    }
  };

  const handlePartnerToggle = (partner: string) => {
    const newPartners = selectedPartners.includes(partner)
      ? selectedPartners.filter(p => p !== partner)
      : [...selectedPartners, partner];
    onPartnersChange(newPartners);
  };

  const selectedPeriodOption = PERIOD_OPTIONS.find(p => p.value === periodType);

  const partnersLabel = selectedPartners.length === 0 
    ? 'Todos' 
    : selectedPartners.length === 1 
      ? selectedPartners[0].charAt(0).toUpperCase() + selectedPartners[0].slice(1).replace('-', ' ')
      : `${selectedPartners.length} seleccionados`;

  // Group period options
  const periodGroups = PERIOD_OPTIONS.reduce((groups, option) => {
    if (!groups[option.group]) groups[option.group] = [];
    groups[option.group].push(option);
    return groups;
  }, {} as Record<string, typeof PERIOD_OPTIONS>);

  // Get period label with custom dates if applicable
  const getPeriodLabel = () => {
    if (periodType === 'custom' && customStart && customEnd) {
      const start = new Date(customStart).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
      const end = new Date(customEnd).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
      return `${start} - ${end}`;
    }
    if (showCustomPicker && periodType !== 'custom') {
      return 'Seleccionar fechas...';
    }
    return selectedPeriodOption?.label || 'Seleccionar';
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Period Filter */}
      <Dropdown
        label="Período"
        value={getPeriodLabel()}
        isOpen={openDropdown === 'period'}
        onToggle={() => toggleDropdown('period')}
        icon="📅"
      >
        <div className="max-h-96 overflow-y-auto">
          {Object.entries(periodGroups).map(([group, options]) => (
            <div key={group}>
              {group !== 'Custom' && (
                <>
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50">
                    {group}
                  </div>
                  {options.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => handlePeriodSelect(option.value)}
                      className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center justify-between ${
                        periodType === option.value && !showCustomPicker
                          ? 'bg-green-50 text-green-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <span>{option.label}</span>
                      {periodType === option.value && !showCustomPicker && (
                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))}
                </>
              )}
            </div>
          ))}
          
          {/* Custom date section */}
          <div className="border-t border-gray-100">
            <button
              onClick={() => handlePeriodSelect('custom')}
              className={`w-full px-4 py-3 text-left text-sm transition-colors flex items-center gap-2 ${
                showCustomPicker || periodType === 'custom'
                  ? 'bg-green-50 text-green-700'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span>📆</span>
              <span>Personalizado</span>
            </button>
            
            {showCustomPicker && (
              <div ref={customPickerRef} className="p-4 bg-gray-50 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Desde</label>
                    <input
                      type="date"
                      value={localStart}
                      onChange={(e) => setLocalStart(e.target.value)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Hasta</label>
                    <input
                      type="date"
                      value={localEnd}
                      onChange={(e) => setLocalEnd(e.target.value)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500"
                    />
                  </div>
                </div>
                <button
                  onClick={handleCustomApply}
                  disabled={!localStart || !localEnd}
                  className="w-full bg-[#00A651] hover:bg-[#008C45] disabled:bg-gray-300 disabled:text-gray-500 text-white rounded-lg py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed"
                >
                  Aplicar fechas
                </button>
                {(!localStart || !localEnd) && (
                  <p className="text-xs text-amber-600 text-center">
                    Selecciona ambas fechas para aplicar
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </Dropdown>

      {/* Partners Filter (unified categories + individual) */}
      {showPartnerFilter && (
        <Dropdown
          label="Partners"
          value={partnersLabel}
          isOpen={openDropdown === 'partners'}
          onToggle={() => toggleDropdown('partners')}
          icon="🏪"
        >
          <div className="max-h-96 overflow-y-auto">
            {/* Select All */}
            <button
              onClick={() => onPartnersChange([])}
              className={`w-full px-4 py-3 text-left text-sm transition-colors flex items-center gap-3 border-b border-gray-100 ${
                selectedPartners.length === 0 ? 'bg-green-50 text-green-700' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                selectedPartners.length === 0 ? 'border-green-500 bg-green-100' : 'border-gray-300'
              }`}>
                {selectedPartners.length === 0 && (
                  <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <span className="font-medium">Todos los partners</span>
            </button>
            
            {/* Categories with partners */}
            {PARTNER_CATEGORIES.filter(cat => cat.id !== 'all').map((category) => {
              const categoryPartners = category.partners;
              const selectedInCategory = categoryPartners.filter(p => selectedPartners.includes(p));
              const allSelected = selectedInCategory.length === categoryPartners.length;
              const someSelected = selectedInCategory.length > 0 && !allSelected;

              return (
                <div key={category.id} className="border-b border-gray-100 last:border-0">
                  {/* Category header (clickable to select all) */}
                  <button
                    onClick={() => handleCategoryToggle(category.id)}
                    className="w-full px-4 py-3 text-left text-sm transition-colors flex items-center gap-3 hover:bg-gray-50"
                  >
                    <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                      allSelected ? 'border-green-500 bg-green-100' : someSelected ? 'border-green-400 bg-green-50' : 'border-gray-300'
                    }`}>
                      {allSelected && (
                        <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                      {someSelected && !allSelected && (
                        <div className="w-2 h-2 bg-green-500 rounded-sm" />
                      )}
                    </div>
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: category.color }}
                    />
                    <span className="font-medium text-gray-800">
                      {category.name}
                    </span>
                    <span className="text-xs text-gray-400 ml-auto">
                      {selectedInCategory.length}/{categoryPartners.length}
                    </span>
                  </button>

                  {/* Individual partners */}
                  <div className="bg-gray-50/50">
                    {category.partners.map((partner) => (
                      <button
                        key={partner}
                        onClick={() => handlePartnerToggle(partner)}
                        className={`w-full pl-12 pr-4 py-2 text-left text-sm transition-colors flex items-center gap-3 ${
                          selectedPartners.includes(partner) 
                            ? 'bg-green-50 text-green-700' 
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                          selectedPartners.includes(partner) 
                            ? 'border-green-500 bg-green-100' 
                            : 'border-gray-300'
                        }`}>
                          {selectedPartners.includes(partner) && (
                            <svg className="w-2.5 h-2.5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                        <span className="capitalize">{partner.replace('-', ' ')}</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Dropdown>
      )}

      {/* Clear filters button */}
      {(selectedPartners.length > 0 || (periodType === 'custom' && customStart && customEnd)) && (
        <button
          onClick={() => {
            onPeriodChange('this_month');
            onPartnersChange([]);
            setLocalStart('');
            setLocalEnd('');
            setShowCustomPicker(false);
          }}
          className="text-xs text-gray-500 hover:text-red-600 transition-colors flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-red-50"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
