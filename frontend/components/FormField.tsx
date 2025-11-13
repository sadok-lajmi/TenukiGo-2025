import React from 'react'
import { useState } from 'react';

const FormField = ({ id, label, type = 'text', value, onChange, placeholder, as = 'input', options = [] }: FormFieldProps) => {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false)

    const filteredOptions = options.filter(option =>
        typeof value === "string"
        ? options.filter(option =>
        option.label.toLowerCase().includes(value.toLowerCase())
        )
        : options
    )

    const handleSelect = (optionValue: string) => {
        onChange({ target: { id: id, value: optionValue } } as any)
        setIsDropdownOpen(false)
    }

    return (
        <div className='form-field'>
            <label htmlFor={id}>{label}</label>

            {as === 'textarea' ? (
                <textarea
                    id={id}
                    name={id}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                />
            ) : as === 'select' ? (
                <select id={id} name={id} value={value} onChange={onChange}>
                    {options.map(({ label, value }) => (
                        <option key={label} value={value}>{label}</option>
                    ))}
                </select>
            ) : as === 'search' ? (
                <div className="relative w-full">
                    <input
                        id={id}
                        name={id}
                        value={value}
                        onChange={onChange}
                        placeholder={placeholder}
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        className="w-full"
                    />
                    {isDropdownOpen && (
                        <ul className='dropdown'>
                            {filteredOptions.length > 0 ? (
                                filteredOptions.map(({ label, value }) => (
                                    <li key={label} onClick={() => handleSelect(value)} className="list-item">
                                        {label}
                                    </li>
                                ))
                            ) : (
                                <li>No {label} found</li>
                            )}
                        </ul>
                    )}
                </div>
            ) : (
                <input
                    type={type}
                    id={id}
                    name={id}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                />
            )}
        </div>
    )
}

export default FormField